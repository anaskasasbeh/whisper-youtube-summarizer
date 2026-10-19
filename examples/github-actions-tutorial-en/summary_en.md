# GitHub Actions Tutorial - Basic Concepts and CI/CD Pipeline with Docker

Source: https://www.youtube.com/watch?v=R8_veQiYBjI

- The tutorial covers GitHub Actions (a platform for automating developer workflows, not only CI/CD), its basic concepts (events → actions → workflow) and benefits such as reducing manual management as projects grow.  
- Typical automation tasks include issue handling, labeling, PR review, releasing versions, generating release notes, and building/testing code.  
- A demo project (Java library using Gradle) shows a full pipeline: commit → GitHub Actions workflow → Gradle build → Docker image → push to a private Docker Hub repository.  
- Workflows are defined in YAML files under `.github/workflows/`; they start on specified **events** (e.g., push to `master`, PR creation) and consist of **jobs** that run on GitHub‑managed runners (Ubuntu, Windows, macOS).  
- Jobs contain ordered **steps** that use pre‑made actions (e.g., `actions/checkout`, `actions/setup-java`) or raw shell commands; a matrix strategy can run the same job on multiple OSes, and the `needs` keyword enforces sequential execution.  
- GitHub‑hosted runners provide the execution environment, so no self‑managed build servers are required; Docker is already installed on Ubuntu runners.  
- To build and push a Docker image, you can either script Docker commands or use a marketplace action such as `docker/build-push-action@v2`, supplying Docker Hub credentials stored as repository **Secrets** (`secrets.<NAME>`).  
- Docker Hub offers one free private repository; the workflow pushes the image (default tag includes the branch name) and the tag can be overridden via the `tag` parameter.  
- Creating a new repository automatically adds an **Actions** tab with workflow templates grouped into Deployment, Continuous Integration, and Publish categories; selecting a template (e.g., “Java Gradle”) generates a starter YAML file that can be edited.  
- The CI workflow demonstrated includes steps: checkout code, set up Java 1.8, make the Gradle wrapper executable, run `gradle build`, then build‑and‑push the Docker image.  
- After committing the workflow to `master`, GitHub Actions shows parallel jobs for each OS (if a matrix is used) and logs for each step, confirming successful builds and image pushes.  
- The presenter plans a broader course on GitHub Actions (deploying to cloud/Kubernetes, Node.js builds, additional automations) and invites feedback and questions.
