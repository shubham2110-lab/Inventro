
# Inventro Final Report

## Team Information

- **Terry Luan** — t.luan@mail.utoronto.ca — Student ID: 1005951427
- **Harsanjam Saini** — harsanjam.saini@mail.utoronto.ca — Student ID: 1007360516
- **Alexander Vicol** — alexander.vicol@mail.utoronto.ca — Student ID: 1008004231
- **Shubham Panchal** — s.panchal@mail.utoronto.ca — Student ID: 1012431067

> Contact emails for any follow-up questions during grading period.

## Motivation

In many small and medium-sized businesses, inventory management is still handled through outdated software or manual spreadsheets that lack real-time synchronization, scalability, and reliability. These systems make it difficult to monitor stock levels accurately across distributed warehouses or retail locations. As a result, manual data entry and disconnected systems frequently lead to stockouts, overstocking, and data inconsistencies, all of which negatively affect operational efficiency and customer satisfaction.

While modern inventory management tools such as Zoho Inventory, Sortly, or Ordoro provide advanced functionality, they can cost hundreds of dollars per month, making them impractical for small teams and startups. Moreover, these third-party SaaS solutions are hosted externally, meaning users often lack full ownership and control over their data. For small businesses that prioritize affordability, customization, and privacy, this remains a significant limitation.

To address these challenges, the team developed **Inventro**, a cloud-native, real-time inventory management system that is reliable, scalable, and self-hosted. Inventro leveraged containerized services to ensure consistent performance, persistent cloud storage to maintain state across restarts and redeployments, and Kubernetes orchestration to provide automated scaling and fault tolerance. The system also incorporated real-time communication and alerting mechanisms (where time permitted) to reduce downtime and support faster, data-driven decision-making for managers and staff.

This project was worth pursuing because it demonstrated core cloud computing concepts—including containerization, orchestration, CI/CD, monitoring, and persistence—in a realistic business context. Inventro not only gave the team hands-on experience with modern cloud technologies but also delivered tangible value by creating an affordable, customizable, and secure inventory management platform tailored to small and medium enterprises.

The target users were warehouse managers, retail operators, and staff in small to medium-sized businesses who required an accessible yet robust solution for tracking inventory across multiple locations. By giving users full control over their deployment, scalability, and data, Inventro aimed to bridge the gap between costly commercial platforms and limited manual systems, offering a practical, high-performance alternative aligned with real business needs and modern cloud-native design principles.

## Objectives

The primary goal of the project was to build and deploy a **stateful, cloud-native web application** that allowed users to create, update, and track inventory items in near real time. The system was designed to use **DigitalOcean Volumes**, **Django**, and **DigitalOcean Kubernetes (DOKS)** to ensure persistent storage, secure access control, and proper data monitoring. This architecture showcased the core principles of **containerization, orchestration, persistence, and observability** required by ECE1779.

Inventro was intended to provide a reliable, scalable, and self-hosted inventory management platform that gives users full control over their data while reducing operational costs. The project also fulfilled ECE1779’s technical learning objectives by integrating persistent storage, automated deployment pipelines, and real-time monitoring into a production-grade system.

### Core Functional & Technical Objectives

The project objectives were:

- **Stateful Web Application:**  
  Build a production-ready inventory management system that supports item CRUD, categorization, carts, and secure access control.

- **Persistent Storage:**  
  Store data in PostgreSQL backed by Persistent Volume Claims (PVCs), ensuring that inventory data survives restarts and rolling updates.

- **Cloud-Native Deployment:**  
  Containerize the application with Docker and deploy it on DigitalOcean Kubernetes (DOKS) using Deployments, Services, and PVCs, with a load-balanced entrypoint.

- **Observability & Monitoring:**  
  Integrate DigitalOcean metrics, Kubernetes logs, and (optionally) Grafana dashboards to monitor CPU, memory, disk usage, and pod health.

- **DevOps & Automation:**  
  Implement CI/CD with GitHub Actions to automate build, test, and deployment of Docker images, and configure automated PostgreSQL backups using a Kubernetes CronJob.

- **Stretch Real-Time Features (optional):**  
  Explore real-time stock updates via Django Channels/WebSockets and serverless email notifications for low-stock alerts. These were treated as stretch goals and implemented partially where time allowed (WebSockets) rather than as core requirements.

Overall, the final system met the core objectives: it was a stateful, containerized, Kubernetes-deployed application with persistent storage, monitoring, CI/CD, and automated backups, closely aligned with the original proposal.

## Technical Stack

- **Frameworks:**  
  Django + Django REST Framework, with HTMX-enhanced templates for lightweight interactivity.

- **Database:**  
  PostgreSQL with Persistent Volume Claims (PVCs) to preserve data across restarts and rolling updates.

- **Containerization:**  
  Docker images and multi-container orchestration via `docker compose` for local development.

- **Orchestration:**  
  Kubernetes (DOKS) with Deployments, Services, Secrets, ConfigMaps, and volume claims; CronJobs for scheduled backups.

- **Storage & Backups:**  
  DigitalOcean Volumes for the database and a DigitalOcean Spaces bucket for automated backup archives.

- **Monitoring:**  
  Provider metrics (DigitalOcean), Kubernetes logs, and optional Grafana dashboards to watch CPU, memory, and pod health.

- **CI/CD:**  
  GitHub Actions workflows that built and pushed images, then applied Kubernetes manifests for consistent releases.

## Features

The final application offered a set of features that directly supported the project objectives and demonstrated the required course technologies.

- **Authentication & Roles:**  
  We implemented secure login using Django’s authentication system. Admin, manager, and staff roles limited what users could see or modify, ensuring that sensitive operations—such as changing stock levels—were restricted to authorized users.

- **Inventory CRUD:**  
  The system supported creating, editing, soft-deleting, and listing items with metadata such as SKU, quantity, cost, location, and category. These operations were available both via the web UI and REST APIs, demonstrating a stateful backend integrated with PostgreSQL.

- **Categorization:**  
  A managed category model kept item organization consistent across the UI and APIs. This provided structured filtering and reporting, which was important for dashboards and low-stock analysis.

- **Carts & Requests:**  
  Users could assemble carts, add or remove items, and submit requests for stock movements through RESTful endpoints. This represented realistic warehouse workflows (e.g., picking orders, internal transfers) and showcased multi-entity state management in the database.

- **Dashboarding:**  
  Server-rendered dashboards summarized available items, recent activity, and quick links to common flows. Dashboards were built using Bootstrap and HTMX, with support for auto-refreshing stats and basic visualizations so operators could see the current state at a glance.

- **Persistence & Resilience:**  
  PostgreSQL data survived pod restarts through PVCs. Backup CronJobs exported snapshots to object storage, providing a recovery path in case of data corruption or accidental deletions.

- **Scalable Delivery:**  
  The same Docker images used for local development via `docker compose` were deployed to Kubernetes with configurable replicas, readiness/liveness probes, and resource limits. This ensured dev/prod parity and demonstrated scalable, cloud-native delivery.

- **Real-Time & Advanced Features (where implemented):**  
  CI/CD pipelines were fully implemented with GitHub Actions. Automated backups ran via a Kubernetes CronJob. WebSocket-based alerts were explored and integrated where feasible to provide near real-time feedback on key events such as stock changes.

Taken together, these features fulfilled the course project requirements: a **stateful**, **containerized** application running on **Kubernetes** with **persistent storage**, **monitoring**, and **at least two advanced features** (CI/CD and automated backups, with optional WebSocket alerts).

## Fulfillment of Course Requirements

<table>
  <tr>
    <td><b>Requirement</b></td>
    <td><b>Implementation in Project</b></td>
  </tr>
  <tr>
    <td>Containerization &amp; Local Dev</td>
    <td>Docker and Docker Compose were used to set up the Django application and PostgreSQL database for local development.</td>
  </tr>
  <tr>
    <td>State Management</td>
    <td>Application state was managed using PostgreSQL with persistent volumes for durable storage.</td>
  </tr>
  <tr>
    <td>Deployment Provider</td>
    <td>The application was deployed on DigitalOcean Kubernetes (DOKS).</td>
  </tr>
  <tr>
    <td>Orchestration</td>
    <td>Kubernetes Deployments, Services, and PersistentVolumeClaims (PVCs) were configured to orchestrate the application components.</td>
  </tr>
  <tr>
    <td>Monitoring</td>
    <td>Monitoring was performed using the DigitalOcean Metrics Dashboard together with Kubernetes logs, with optional Grafana dashboards.</td>
  </tr>
  <tr>
    <td>Advanced Features (≥2)</td>
    <td>CI/CD was implemented with GitHub Actions, automated backups were configured via a Kubernetes CronJob, and WebSocket-based alerts were explored as an optional enhancement.</td>
  </tr>
</table>

The project scope was realistic for a four-person team within the 5-week course timeline. Each team member focused on one major subsystem (frontend, backend, architecture, and DevOps), which enabled efficient parallel development. The system’s modular design allowed incremental feature integration while maintaining a deployable state throughout the project.

Optional features (such as serverless components and WebSockets) were only addressed after the core milestones had been completed, ensuring that the primary deliverables were prioritized. This approach allowed the team to deliver a fully functional, containerized, and monitored stateful application by the due date while demonstrating mastery of all required course technologies.

The final system satisfied all course technical requirements and maintained a realistic and achievable scope. The objectives were specific and mapped directly to the ECE1779 course technologies: a containerized application with local development using Docker and Docker Compose, deployment on Kubernetes, PostgreSQL with persistent storage, provider-based monitoring, and at least two advanced features (continuous integration and deployment, automated backups, and real-time alerts where implemented). The scope was deliberately sized for a four-person team and the project timeline.

## Architecture Overview

1. **Frontend:**  
   Bootstrap-based templates with HTMX enhancements kept page loads fast while avoiding a heavy SPA. The UI consumed REST APIs where appropriate and used partial HTML updates for responsive interactions.

2. **Backend:**  
   Django REST Framework exposed APIs for inventory, cart management, and authentication, while Django admin enabled operational oversight. Business logic for permissions, validation, and inventory rules was centralized in the backend.

3. **Data Layer:**  
   PostgreSQL stored transactional data, including users, items, categories, and carts. Django migrations tracked schema changes over time. Persistent volumes bound the database to durable disk in the Kubernetes cluster.

4. **Platform:**  
   Docker images encapsulated the application and its dependencies. Kubernetes Deployments managed rollouts and scaling, Services exposed HTTP entrypoints, and CronJobs handled scheduled backups to object storage.

5. **Observability:**  
   Provider metrics and Kubernetes logs were used to monitor resource usage and application health. This observability allowed the team to diagnose performance issues, tune resource requests/limits, and verify that rollouts were proceeding smoothly.

![ERD diagram showing key relationships](assets/images/entity_relationships.png)


## User Guide

1. **Sign up or log in.**  
   Access is role-gated; managers and admins can create and manage inventory, while staff can browse and submit cart requests.

2. **Create categories.**  
   Use the admin area or API to define categories so items remain organized by type, location, or business unit.

3. **Add inventory items.**  
   Supply name, SKU, quantity, cost, and location. Items appear immediately on dashboards and via the API.

4. **Edit or retire items.**  
   Update quantities as stock moves, or mark items inactive to hide them from active lists without losing history.

5. **Build carts.**  
   Add items to a cart through the UI or API to request pulls or transfers. Remove lines or clear a cart as needed.

6. **Monitor status.**  
   Use dashboards for day-to-day visibility into stock levels and recent activity. Operators can also review Kubernetes metrics when investigating performance or availability.

## Development Guide

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ with `pip`
- Access credentials for PostgreSQL and any third-party stores (see `.env` templates)

### Local Setup

1. **Clone the repository** and create a virtual environment:  
   `python -m venv .venv && source .venv/bin/activate`

2. **Install dependencies:**  
   `pip install -r requirements.txt`

3. **Create environment files** from the provided templates (e.g., database URL, secret key, object storage credentials).

4. **Start services locally:**  
   `docker compose -f compose.dev.yml up --build`  
   This launches Django, PostgreSQL, and supporting services.

5. **Run migrations and create a superuser:**  
   `docker compose -f compose.dev.yml exec web python manage.py migrate`  
   then  
   `docker compose -f compose.dev.yml exec web python manage.py createsuperuser`

6. **Access the app:**  
   Open `http://localhost:8000` for the UI or `http://localhost:8000/api/` for REST endpoints.

### Testing

- **Unit tests:**  
  Run `pytest` inside the web container or virtual environment.

- **API checks:**  
  Use `curl` or Postman against the `/api/` routes for inventory and carts.

- **Static analysis (optional):**  
  Run tools such as `flake8` and `isort` locally to maintain formatting and style consistency.

## Deployment Information

- **Container registry:**  
  Built images are tagged and pushed by GitHub Actions to the configured container registry (e.g., DigitalOcean Container Registry).

- **Kubernetes manifests:**  
  Manifests reside in `k8s/` with namespaced Deployments, Services, and PVC claims. Apply them via:  
  `kubectl apply -k k8s/`.

- **Backup CronJob:**  
  `k8s/cronjob-backup.yaml` defines a scheduled job that exports PostgreSQL dumps to object storage (DigitalOcean Spaces) on a schedule, with retention controls documented in the repo.

- **Ingress:**  
  Production traffic terminates at a cloud load balancer that forwards requests to the Kubernetes Service for the web app.

- **Live URL:**  
  Provide the cluster or load balancer URL here, for example:  
  `https://inventro.example.com`.

## Individual Contributions

The project tracked four members. Summaries below describe the main areas each member owned or significantly contributed to.

### Terry Luan

Terry led the core backend integration and deployment foundations for Inventro. His main contributions included:

- **Project Bootstrap & Core Apps**
  - Initialized the Django project and key apps (`inventory`, `cart`, `orders`, `users`).
  - Integrated **Django REST Framework** and implemented the initial API endpoints for items and carts.
  - Created and maintained `requirements.txt` to standardize dependencies for local development, Docker builds, and CI.

- **Inventory, Auth & Cart Integration**
  - Migrated and wired up the **inventory** and **login** pages to the Django backend.
  - Connected the inventory table to the backend so items, pagination, and metadata are served from PostgreSQL.
  - Introduced a dedicated authentication/users app and set `LOGIN_URL` in `settings.py`, cleaning up how user data and login flows are handled.
  - Fixed multiple UI/UX issues (login page, sidebar highlighting, back button routing, naming consistency from “products” to “inventory”).
  - Reviewed and **merged the `cart_page` branch**, ensuring the cart UI was correctly hooked up to the existing models, views, and templates.

- **Data Seeding & Populate Scripts**
  - Authored and iteratively refined database populate scripts (`populate.py`, `populate_database.py`) to seed items and metadata for testing.
  - Added support for **cost** and **location** fields in the populate logic to match the evolving Item model.
  - Hooked database population into `entrypoint.sh` and adjusted Docker Compose startup so developers could get a usable environment with realistic test data in one command.

- **Docker, Nginx & Local Dev Experience**
  - Fixed and stabilized the **Dockerfile** and web container configuration.
  - Introduced an Nginx container and related configuration to support a more production-like setup.
  - Reorganized the Django code into an inner `inventro` directory to simplify imports and deployment.
  - Added separate **dev and prod Docker Compose files** and tuned volumes so code changes reflect correctly in the dev environment.

- **Kubernetes Manifests, CronJob & Repo Integration**
  - Added and refactored Kubernetes manifests, including Nginx objects and namespace changes to `inventro`, and split components into clear YAML files (deployments, services, etc.).
  - **Implemented and later fixed the PostgreSQL backup CronJob Kubernetes file**, ensuring scheduled dumps to object storage work as intended.
  - Authored and reviewed multiple merge commits (e.g., integrating Shubham’s CI/CD + Kubernetes work, Alex’s RBAC/metadata branch, and the cart feature branch), resolving conflicts and keeping the `main` branch deployable.

Overall, Terry owned the backbone of the project: he turned a bare Django app into a working, containerized service with connected front-end pages, realistic seed data, a functioning backup CronJob, and a clean path to Kubernetes deployment.

### Harsanjam Saini

- **Dashboard UX & Live Telemetry:**  
  Built the dashboard and analytics screens with Bootstrap cards, chart canvases, and activity feeds so operations staff received instant status at login. Stat components and chart placeholders paired with auto-refreshing JavaScript that pulled `/api/stats/` and `/api/metrics/` on a fixed interval, keeping counts, category charts, and trend lines current without manual refreshes.

- **Inventory CRUD Ergonomics:**  
  Implemented HTMX-driven search, filtering, pagination, and row actions in the inventory table so managers could slice data by status or category and edit or delete items in place. Safeguards like confirmation prompts and force-delete handling reduced accidental data loss while keeping workflows fast.

- **Metrics & Activity APIs:**  
  Added REST endpoints that aggregated low-stock counts, valuation, trend data, and recent item activity, allowing the frontend charts to display real operational data. These APIs computed rollups across categories and time buckets, providing the quantitative backbone for the live dashboard experience.

### Alexander Vicol

<!-- TODO: Replace this placeholder with Alexander's actual contributions. -->

_Contribution summary to be added_

### Shubham Panchal

<!-- TODO: Replace this placeholder with Shubham's actual contributions. -->

_Contribution summary to be added_

## Lessons Learned and Concluding Remarks

- Containerizing early simplified local onboarding and kept dev/prod parity high, minimizing surprise regressions.
- Kubernetes provided resilience and rollback safety but required disciplined secret management and careful resource tuning to remain cost-effective.
- Automated backups and CI/CD pipelines acted as critical guardrails; investing in them reduced risk more than any single application feature.
- Lightweight HTMX interactions paired well with Django, enabling the team to ship usable screens without the overhead of a full SPA.
- Overall, the project showed how a small team can retain ownership of data and infrastructure while still achieving reliability, observability, and a smooth user experience in a cloud-native environment.
