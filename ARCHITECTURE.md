# Architecture

## Overview

Answer Sheet Reader is a Django application that receives answer-sheet images, delegates image recognition to a native C/C++ library, lets the user review the recognized data, and persists the confirmed result.

The system is intentionally split between the web application and the image-processing component.

## Components

### Django application

Responsibilities:

- authentication and user profiles;
- upload and review workflow;
- authorization of user-owned records;
- score calculation;
- persistence;
- HTML rendering;
- health reporting.

### PostgreSQL

Stores application data, including:

- users and profiles;
- uploaded image bytes;
- recognition state;
- confirmed answer-sheet data;
- scores.

SQLite is used as a fallback for local development and automated tests when PostgreSQL is not configured.

### Native image-processing library

The application loads `libleitor.so` through Python's `ctypes`.

The native boundary is isolated in:

```text
leitor_projeto/App/biblioteca.py
```

The library receives an image path and returns a structured result containing the exam identifier, participant identifier, recognized answers and error state.

### Container runtime

Docker Compose runs:

- the Django/Gunicorn service;
- PostgreSQL.

PostgreSQL exposes a health check and the web service waits for the database to become healthy before starting. The application itself exposes `/health/`, which verifies database connectivity.

## Request flow

### Image submission

1. An authenticated user submits an image.
2. Django validates that an image was provided.
3. Pillow opens the uploaded image and normalizes the temporary processing input to PNG.
4. A temporary file is created.
5. The native library processes that file.
6. Django stores the original uploaded bytes and the initial recognition result.
7. The user receives a review form.

### Review and scoring

1. The user reviews the recognized identifiers and answers.
2. Django validates the submitted form.
3. The answer sequence is compared with the configured answer key.
4. A score is calculated.
5. The confirmed result is persisted.
6. The original upload is marked as confirmed.

## Data model

### Perfil

One-to-one extension of the Django user model with profile information and an optional profile image.

### ImagemUpload

Represents an uploaded answer-sheet image and its confirmation state.

Each upload belongs to a user.

### DadosImagem

Represents the confirmed recognition result.

Each result belongs to:

- one user;
- one uploaded image.

The image/result relationship is one-to-one.

## Native boundary

Using `ctypes` keeps the Django layer independent from the C/C++ implementation while allowing CPU-oriented image-processing code to remain native.

Current trade-offs:

- the native shared objects are Linux-specific;
- the web process invokes recognition synchronously;
- failures at the native boundary must be converted into application-level errors.

For a higher-throughput deployment, recognition could be moved behind an asynchronous job queue so HTTP workers do not remain occupied while images are processed.

## Reliability

Implemented:

- database-aware health endpoint;
- PostgreSQL container health check;
- web startup dependency on database readiness;
- Gunicorn instead of Django's development server;
- automated Django tests in GitHub Actions;
- local SQLite fallback for tests and development.

Potential future improvements:

- structured application logs;
- request and job metrics;
- tracing;
- retry policy for asynchronous processing;
- object storage for uploaded images;
- database backups;
- readiness and liveness probes separated by purpose.

## Security

Implemented:

- Django authentication;
- ownership filtering when users access images and results;
- CSRF protection through Django templates;
- Django password validation during registration;
- configuration and secrets through environment variables;
- generic client-facing processing errors while detailed exceptions are logged server-side.

Production deployments should additionally enforce HTTPS, secure cookies, a non-development secret key, restricted allowed hosts and external secret management.

## Scaling path

The current architecture is suitable for a small deployment and portfolio demonstration.

A possible evolution for larger traffic would be:

```text
Client
  |
Load Balancer
  |
Django API / Web
  |--------- PostgreSQL
  |--------- Object Storage
  |
Job Queue
  |
Image Processing Workers
  |
Native C/C++ Recognition
```

This would separate request handling from CPU-heavy recognition and allow the web tier and worker tier to scale independently.

## Testing

The automated suite currently covers:

- scoring behavior;
- core persistence relationships;
- rejection of weak registration passwords;
- creation of users and profiles with valid credentials;
- health endpoint behavior.

The suite runs on every push and pull request through GitHub Actions.
