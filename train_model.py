"""
train_model.py - trains the brain tumor CNN and saves it for the backend.

Usage (from the training folder):
    python train_model.py
    python train_model.py --dataset ../dataset --epochs 40 --batch-size 32

Dataset layout: any folder tree whose image folders are named like
    yes / no            (Kaggle "Brain MRI Images for Brain Tumor Detection")
    tumor / no_tumor
    glioma, meningioma, pituitary, notumor   (4-class Kaggle set, merged into 2 classes)
See dataset/README.md for details.
"""
import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from PIL import Image
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import train_test_split
from tensorflow import keras
from tensorflow.keras import layers

IMG_SIZE = 128  # must match backend/predict.py
SEED = 42
ALLOWED_FORMATS = {"JPEG", "PNG", "BMP"}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
NEGATIVE_FOLDERS = {"no", "no_tumor", "notumor", "no-tumor", "non_tumor", "normal", "healthy"}
POSITIVE_FOLDERS = {"yes", "tumor", "tumour", "brain_tumor", "glioma", "meningioma", "pituitary",
                    "glioma_tumor", "meningioma_tumor", "pituitary_tumor"}


# ---------------------------------------------------------------- preprocessing
def preprocess_image(path: Path) -> np.ndarray:
    """Same steps as backend/predict.py: RGB -> 128x128 bilinear resize -> float 0-255.
    (Scaling to 0-1 happens inside the model with a Rescaling layer.)"""
    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)
        return np.asarray(img, dtype=np.uint8)


# ---------------------------------------------------------------------- dataset
def load_dataset(dataset_dir: Path):
    """Walk the dataset folder, label images by their parent folder name."""
    images, labels, skipped = [], [], 0
    for path in sorted(dataset_dir.rglob("*")):
        if path.suffix.lower() not in EXTENSIONS or path.name.startswith("._") or "__MACOSX" in path.parts:
            continue
        folder = path.parent.name.lower().replace(" ", "_")
        if folder in NEGATIVE_FOLDERS:
            label = 0
        elif folder in POSITIVE_FOLDERS:
            label = 1
        else:
            continue
        try:
            with Image.open(path) as probe:
                if probe.format not in ALLOWED_FORMATS:
                    raise ValueError("unsupported format")
            images.append(preprocess_image(path))
            labels.append(label)
        except Exception:
            skipped += 1
    if skipped:
        print(f"Skipped {skipped} unreadable image(s).")
    x, y = np.array(images, dtype=np.uint8), np.array(labels, dtype=np.float32)
    if len(x) == 0 or len(set(y)) < 2:
        raise SystemExit(
            f"Could not find images for both classes in '{dataset_dir}'.\n"
            "Expected folders named e.g. 'yes' and 'no' (see dataset/README.md)."
        )
    return x, y


def make_split(x, y):
    """70% train / 15% validation / 15% test, stratified so each split keeps the class ratio."""
    idx = np.arange(len(x))
    train_val, test = train_test_split(idx, test_size=0.15, stratify=y, random_state=SEED)
    train, val = train_test_split(train_val, test_size=0.1765, stratify=y[train_val], random_state=SEED)
    return train, val, test


def to_dataset(x, y, batch_size, shuffle):
    ds = tf.data.Dataset.from_tensor_slices((x, y))
    if shuffle:
        ds = ds.shuffle(len(x), seed=SEED, reshuffle_each_iteration=True)
    ds = ds.batch(batch_size).map(lambda a, b: (tf.cast(a, tf.float32), b), num_parallel_calls=tf.data.AUTOTUNE)
    return ds.prefetch(tf.data.AUTOTUNE)


# ------------------------------------------------------------------------ model
def build_model() -> keras.Model:
    augmentation = keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.08),
            layers.RandomZoom(0.1),
            layers.RandomContrast(0.1),
        ],
        name="augmentation",  # only active during training
    )
    inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="mri_image")
    x = layers.Rescaling(1.0 / 255, name="rescale")(inputs)
    x = augmentation(x)
    for filters in (32, 64, 128, 128):
        x = layers.Conv2D(filters, 3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D()(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(0.5)(x)
    outputs = layers.Dense(1, activation="sigmoid", name="tumor_probability")(x)
    model = keras.Model(inputs, outputs, name="brain_tumor_cnn")
    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy", keras.metrics.AUC(name="auc")],
    )
    return model


# ------------------------------------------------------------------------ plots
def save_plots(history, cm, out_dir: Path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(history.history["accuracy"], label="train")
    axes[0].plot(history.history["val_accuracy"], label="validation")
    axes[0].set_title("Accuracy"); axes[0].set_xlabel("epoch"); axes[0].legend()
    axes[1].plot(history.history["loss"], label="train")
    axes[1].plot(history.history["val_loss"], label="validation")
    axes[1].set_title("Loss"); axes[1].set_xlabel("epoch"); axes[1].legend()
    fig.tight_layout(); fig.savefig(out_dir / "training_curves.png", dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], ["No Tumor", "Tumor"]); ax.set_yticks([0, 1], ["No Tumor", "Tumor"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title("Confusion matrix (test set)")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.tight_layout(); fig.savefig(out_dir / "confusion_matrix.png", dpi=120); plt.close(fig)


# ------------------------------------------------------------------------- main
def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Train the brain tumor CNN")
    parser.add_argument("--dataset", type=Path, default=root / "dataset")
    parser.add_argument("--output-dir", type=Path, default=root / "model")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    random.seed(SEED); np.random.seed(SEED); keras.utils.set_random_seed(SEED)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading images from {args.dataset} ...")
    x, y = load_dataset(args.dataset)
    print(f"Loaded {len(x)} images  (tumor: {int(y.sum())}, no tumor: {int(len(y) - y.sum())})")

    tr, va, te = make_split(x, y)
    train_ds = to_dataset(x[tr], y[tr], args.batch_size, shuffle=True)
    val_ds = to_dataset(x[va], y[va], args.batch_size, shuffle=False)
    test_ds = to_dataset(x[te], y[te], args.batch_size, shuffle=False)
    print(f"Split -> train: {len(tr)}, validation: {len(va)}, test: {len(te)}")

    # Give the rarer class a larger weight so the model does not just predict the majority class.
    n0, n1 = np.sum(y[tr] == 0), np.sum(y[tr] == 1)
    class_weight = {0: len(tr) / (2 * n0), 1: len(tr) / (2 * n1)}

    model = build_model()
    model.summary()
    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-5),
    ]
    history = model.fit(train_ds, validation_data=val_ds, epochs=args.epochs, shuffle=False,
                        class_weight=class_weight, callbacks=callbacks, verbose=2)

    # ---- evaluation on the untouched test set
    probs = model.predict(test_ds, verbose=0).reshape(-1)
    y_true, y_pred = y[te].astype(int), (probs >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)) * 100, 2),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)) * 100, 2),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)) * 100, 2),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)) * 100, 2),
        "confusion_matrix": cm.tolist(),  # [[TN, FP], [FN, TP]]
        "train_images": int(len(tr)),
        "validation_images": int(len(va)),
        "test_images": int(len(te)),
        "epochs_trained": len(history.history["loss"]),
        "image_size": IMG_SIZE,
        "parameters": int(model.count_params()),
        "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    print("\n=== Test-set results ===")
    for key in ("accuracy", "precision", "recall", "f1_score"):
        print(f"{key:>10}: {metrics[key]:.2f} %")
    print("confusion matrix [[TN, FP], [FN, TP]]:", metrics["confusion_matrix"])

    model.save(args.output_dir / "brain_tumor_model.keras")
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    save_plots(history, cm, args.output_dir)
    print(f"\nSaved model, metrics.json and plots to {args.output_dir}")


if __name__ == "__main__":
    main()
