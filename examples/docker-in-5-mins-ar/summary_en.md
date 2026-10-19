# دوكر في 5 دقائق | Docker in 5 mins

Source: https://www.youtube.com/watch?v=yRkE-1Lq0qo

- Running code on your own machine may work, but on another machine it can fail due to different environment versions (e.g., your code uses Node 18 while the other machine has Node 14, causing many errors).  
- The problem worsens when switching operating systems (e.g., from Windows to Linux), leading to incompatibility and numerous errors beyond simple version mismatches.  
- **Virtual machines (VMs)** solve this by packaging an entire OS plus all required tools and libraries into a single “VM snapshot,” ensuring the same environment runs everywhere.  
- VMs are heavy because they contain a full OS, resulting in large file sizes and high resource consumption.  
- **Docker** offers a lighter solution: instead of bundling a whole OS, it packages only the application code and its dependencies into a **Docker image**.  
- Docker containers run on the host’s Docker Engine, not on a full OS, making them much smaller and faster than VMs while still providing consistent execution across any host OS.  
- To start using Docker, download the appropriate Docker Desktop version from docker.com for your OS (e.g., Docker for Windows).  
- Inside your project, create a **Dockerfile** that lists the commands needed to build the image and copy project files (e.g., `server.js` or `index.js`) into the image.  
- Build the image by running `docker build` in a terminal; Docker reads the Dockerfile, executes the commands, and produces a Docker image.  
- Run a container from the image either by clicking “Play” in Docker Desktop or by executing `docker run -it <image-name>` in the terminal.  
- This workflow lets you develop once and run the same container on any machine without version or OS conflicts.  
- The entire process—from writing a Dockerfile to building an image and launching a container—can be completed in under five minutes.
