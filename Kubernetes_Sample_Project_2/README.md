# Kubernetes & Docker Project Notes: Test Application

This document serves as a comprehensive reference guide and set of notes for this project. It outlines the structure, prerequisites, and all the critical Docker and Kubernetes commands used, complete with reasoning and context for future implementations.

## Project Structure Explained

- `app.py`: The entry point for the Flask web application. It serves a simple HTML page that accepts a user's name and displays a welcome message.
- `dockerfile`: Contains the step-by-step instructions to assemble the Docker image. This is our blueprint for containerization.
- `requirements.txt`: Specifically lists Python dependencies (like Flask) required by our backend application to run successfully in an isolated environment.
- `deployment.yaml`: The Kubernetes manifest file. It defines both a `Deployment` (to run the application pods) and a `Service` (to make the app accessible via a network).
- `templates/` & `static/`: Contains the HTML templates and static assets (CSS/JS) for our Flask frontend.

## 🐳 Docker Command Reference

Docker is used to package the application along with its environment so it behaves consistently regardless of where it runs.

### 1. Building the Image
```bash
docker build -t kubernetes-test-app:latest .
```
- **Why we use it:** This command reads the `dockerfile` in the current directory (`.`) and bundles our application code, dependencies, and base OS into a single portable artifact called an "image."
- **Notes:** The `-t` flag tags the image with a name (`kubernetes-test-app`) and a version (`latest`), making it easier to reference when deploying.

### 2. Testing Locally (Optional)
```bash
docker run -p 5000:5000 kubernetes-test-app:latest
```
- **Why we use it:** This stands up a container based on the image we just built. It allows us to verify the application actually works in an isolated Docker environment before attempting to deploy it to the more complex Kubernetes environment.
- **Notes:** The `-p` flag maps the port on your physical computer to the port exposed inside the container.

---

## ☸️ Kubernetes Command Reference

Kubernetes is used to orchestrate our containers. It ensures the application is highly available, scales seamlessly, and handles self-healing if a container crashes.

### 1. Starting the Cluster
```bash
minikube start
```
- **Why we use it:** Minikube sets up a lightweight, single-node Kubernetes cluster directly on your local machine. You need a running cluster to deploy your Kubernetes resources.
- **Notes:** Without this running, `kubectl` commands will output errors like "machine actively refused it" because the control plane isn't available.

### 2. Applying the Manifest
```bash
kubectl apply -f deployment.yaml
```
- **Why we use it:** This is the core declarative command. It tells Kubernetes to take the desired state defined in `deployment.yaml` and make it a reality. It will spawn the pods (containers) and create the service network.
- **Notes:** `apply` is extremely useful because if you make changes to your YAML later, running `apply` again will gracefully update existing resources without needing to delete them first.

### 3. Monitoring Pods
```bash
kubectl get pods
```
- **Why we use it:** Used to check the exact status of your application instances. Are they running? Crashing? Still downloading the image? 
- **Notes:** You can add `-w` (watch) at the end to stream status changes in real-time.

### 4. Viewing Logs
```bash
kubectl logs <pod-name>
```
- **Why we use it:** If a pod crashes or the application isn't behaving properly, this allows you to peek into the standard output of the application to see errors (like Python tracebacks).

### 5. Exposing the Service Connectively
```bash
minikube service kubernetes-test-app
```
- **Why we use it:** By default, Kubernetes services (NodePorts or ClusterIPs) are isolated inside the cluster's private network. Minikube provides this helper command to map the cluster IP to a reachable URL on your host browser.
- **Notes:** This is the easiest way to immediately test your application via a browser. Note that this command will block the terminal while running.

### 6. Alternative Access (Port Forwarding)
```bash
kubectl port-forward service/kubernetes-test-app 8080:8080
```
- **Why we use it:** A native Kubernetes way to pipe a local port (like an SSH tunnel) directly into the Kubernetes service, bypassing complex networking overlays.
- **Notes:** This is universally available on any Kubernetes cluster (unlike `minikube service` which only works locally).

### 7. Cleaning Up
```bash
kubectl delete -f deployment.yaml
```
- **Why we use it:** Shuts down all resources (Deployments, Pods, Services) that were created by the YAML file.
- **Notes:** Essential for tearing down an environment when you are done to save CPU and memory resources on your machine.
