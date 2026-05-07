# Docker Demonstration App

A modern, visually appealing Flask web application designed for Docker containerization demonstrations. This application features a premium dark glassmorphism UI, smooth micro-animations, and dynamic frontend interactions handling a simple greeting workflow.

## Features

- **Flask Backend**: Lightweight python web server handling form submissions and dynamic viewing.
- **Modern Glassmorphism UI**: High-end styling utilizing dark mode, translucent panels, deep drop shadows, and backdrop blurs.
- **Animated Frontend**:
  - Smooth continuous gradient CSS background animations.
  - Interactive form validation with Javascript "shake" feedback.
  - Real-time Confetti particle effects created via vanilla JS Web Animations API.
- **Cache-busting Integrations**: Versioned static references (`?v=2`) bypassing aggressive browser caching.

## Project Structure

```text
MLOPS-DOCKER/
│
├── app.py                  # Main Flask backend module
├── requirements.txt        # Python dependencies list
├── README.md               # Project documentation
├── templates/              # HTML view definitions
│   ├── index.html          # Data entry form
│   └── greet.html          # Final greeting view
└── static/                 # Static web resources
    ├── css/
    │   └── style.css       # Core styling & keyframes
    └── js/
        └── main.js         # Browser-side effects & logic
```

## Local Setup & Installation

Follow these steps to run the application directly on your local system:

1. **Navigate to the directory**:
   ```bash
   cd MLOPS-DOCKER
   ```

2. **Setup your environment (Optional but Recommended)**:
   ```bash
   python -m venv venv
   # Depending on your OS, activate the environment:
   # Windows: venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask App**:
   ```bash
   python app.py
   ```

5. **Interact**:
   Open your browser and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
