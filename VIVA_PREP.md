# Viva preparation

## A. Project explanation (2-3 minutes)

"My project is a Brain Tumor Detection System - an educational web app that
predicts whether a brain MRI slice looks like it contains a tumor.

It's a full-stack app. The frontend is built with React and Vite: a user
drags in an MRI image, sees a preview, and clicks a button to analyze it.
That image is sent to a Flask backend I built as a REST API. The backend
validates the file, resizes it to 128 by 128 pixels, and feeds it into a
convolutional neural network I trained myself using TensorFlow and Keras.

The CNN has four convolution blocks that progressively extract visual
features - edges, textures, shapes - and end in a single sigmoid output: a
probability from 0 to 1 of the image showing a tumor. I trained it on a
public Kaggle brain-MRI dataset, using a 70/15/15 train-validation-test
split, data augmentation to reduce overfitting on a small dataset, and early
stopping so training halts once the validation loss stops improving.

The result comes back as JSON with a prediction label and a confidence
percentage, which the frontend displays alongside the model's own test-set
accuracy for transparency. I was careful to frame this as an educational
prediction, not a medical diagnosis, both in the UI copy and in the API
response itself.

The whole thing is deployed live: the frontend on Vercel, the backend in a
Docker container on Hugging Face Spaces, communicating over a REST API with
CORS locked down to just my frontend's domain."

## B. Technical viva questions

1. **What is a CNN and why use it for images?**
   A neural network with layers that slide learned filters across the image
   to detect local patterns (edges, textures) and combine them into
   higher-level features. It reuses the same filter across the whole image,
   which is far more parameter-efficient than a fully-connected network for
   image data.

2. **Why TensorFlow/Keras specifically?**
   Keras gives a concise, readable model-building API, has first-class
   TensorFlow support, and is the most common choice in coursework, so it's
   easy to explain and well documented.

3. **What does the `Rescaling` layer do?**
   Divides pixel values by 255 so the network sees inputs in the 0-1 range,
   which trains more stably than raw 0-255 values.

4. **What is data augmentation and why use it here?**
   Randomly flipping, rotating, zooming, and adjusting contrast on training
   images each epoch, so the model sees more variation than the raw dataset
   contains. It reduces overfitting, which matters a lot on a small medical
   imaging dataset.

5. **What is the train/validation/test split for?**
   Train: what the model learns from. Validation: monitored during training
   to tune and to trigger early stopping, without ever being learned from
   directly. Test: held out completely until the end, to get an honest,
   unbiased accuracy estimate.

6. **What is overfitting, and how did you guard against it?**
   When a model memorizes the training data instead of learning general
   patterns, so it performs well on training data but poorly on new data. I
   used data augmentation, dropout, batch normalization, and early stopping.

7. **What does Dropout do?**
   Randomly disables a fraction of neurons during training, forcing the
   network to not rely on any single neuron and reducing overfitting.

8. **What is Batch Normalization?**
   Normalizes each layer's activations within a batch, which stabilizes and
   speeds up training.

9. **What loss function did you use, and why?**
   Binary cross-entropy, the standard loss for two-class (tumor / no tumor)
   classification with a sigmoid output.

10. **What does the sigmoid output actually represent?**
    A single probability between 0 and 1 that the image belongs to the
    positive ("tumor") class; I threshold it at 0.5 to pick a label and use
    its distance from 0.5 as the confidence score.

11. **How did you evaluate the model?**
    On the held-out test set, using accuracy, precision, recall, F1 score,
    and a confusion matrix - not just accuracy, since a dataset skewed
    toward one class can make accuracy alone misleading.

12. **What's the difference between precision and recall here?**
    Precision: of the images flagged "tumor", how many actually were.
    Recall: of the actual tumor images, how many did the model catch. In a
    medical context recall matters more, since missing a real tumor
    (false negative) is more costly than a false alarm.

13. **Why class weighting in training?**
    If one class has more images than the other, the model can get high
    accuracy by mostly predicting the majority class. Class weights make
    mistakes on the minority class cost more during training, keeping the
    model balanced.

14. **What is the REST API and what does POST /predict do?**
    A stateless HTTP interface where each endpoint represents a resource or
    action. `POST /predict` accepts an uploaded image as multipart form
    data, runs it through the preprocessing and model, and returns a JSON
    prediction.

15. **Why Flask instead of Django or FastAPI?**
    Flask is minimal and unopinionated, which keeps a small single-purpose
    API easy to read end-to-end - appropriate for a project this size, with
    less boilerplate than Django and a gentler learning curve than async
    FastAPI patterns for a student.

16. **How do you handle a bad or corrupted upload?**
    The file extension is checked, then Pillow attempts to open and
    `verify()` the image; anything that fails returns a `400` with a clear
    error message before the file ever reaches the model.

17. **How does the frontend talk to the backend, and how do you avoid
    hardcoding localhost in production?**
    Through `fetch()` calls in `src/api.js`, using a base URL read from the
    `VITE_API_URL` environment variable, which is set per-environment (a
    local `.env.development` file for development, a Vercel dashboard
    variable for production) rather than hardcoded.

18. **What is CORS, and how did you configure it?**
    Cross-Origin Resource Sharing controls which website origins a browser
    is allowed to make requests from to your API. I restrict it with
    `Flask-CORS` to only the deployed frontend's exact origin, via the
    `CORS_ORIGINS` environment variable, rather than allowing all origins.

19. **How would you deploy this, and why not put TensorFlow in a serverless
    function?**
    Frontend on Vercel (static build). Backend in a small always-on Docker
    container (Hugging Face Spaces or Render), because TensorFlow's package
    size exceeds most serverless function size limits and benefits from
    staying loaded in memory between requests instead of a cold start.

20. **What are the limitations of this project?**
    Trained on a small public dataset so it won't generalize to every
    scanner or imaging protocol, gives no tumor location or type, has not
    been clinically validated, and is not a substitute for a radiologist -
    explicitly framed as educational throughout the app.

## C. Architecture explanation

`Frontend (React) → HTTP POST multipart/form-data → Backend (Flask) →
in-memory validation & resize → CNN (Keras) → JSON response → Frontend
renders result`. No uploaded image is ever written to disk; everything
happens in memory for the lifetime of one request.

## D. Future improvements

See the README's "Future improvements" section - larger datasets,
multi-class classification, explainable AI (Grad-CAM), transfer learning,
k-fold cross-validation, and user history.
