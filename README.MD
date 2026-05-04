# aws-data-platform-structure

A reusable blueprint for structuring serverless data platforms on AWS — Lambda + Glue, with shared utilities packaged once and consumed by both runtimes.

This repo is the companion code for the article **[Structuring a Serverless Data Platform on AWS: A Reusable Blueprint for Lambda and Glue](https://raguvind.com/writing/aws-serverless-data-platform)**.

---

## What this demonstrates

The "one source, two packagings" pattern. A single `service_core` Python module is packaged two ways:

- **Lambda Layer** — published from `service_core/serverless.yml`, attached to Lambda functions
- **Glue library ZIP** — built from the same source, uploaded to S3, referenced by Glue jobs via `--extra-py-files`

Both runtimes import the shared code through the same import path:

```python
from service_core.utils.logger import get_logger
```

The job code does not know whether it runs in Lambda or Glue. Packaging is invisible at the import boundary.

---

## Repository layout

```
aws-data-platform-structure/
│
├── build-scripts/              # Helper scripts for build and packaging
│   ├── file-helper.js
│   └── initialize.js           # Builds Layer ZIP + Glue library ZIP from service_core/
│
├── service_core/               # Shared core: logging, repositories, config
│   ├── repositories/
│   │   ├── athena_repository.py
│   │   └── dynamodb_repository.py
│   ├── utils/
│   │   └── logger.py           # JsonFormatter + get_logger
│   └── serverless.yml          # Publishes Lambda Layer + uploads Glue ZIP to S3
│
├── demo-micro_service/         # Example microservice consuming service_core
│   ├── lambdas/
│   │   └── hello_world_lambda.py
│   ├── glue_jobs/
│   │   └── hello_world_data_extractor.py
│   └── serverless.yml          # Lambda function + Glue job definitions
│
├── serverless-compose.yml      # Orchestrates deployment order across services
├── package.json
└── README.MD
```

---

## How it works

### 1. Compose orchestrates deployment order

```yaml
# serverless-compose.yml
services:
  service-core:
    path: ./service_core
  demo-micro-service:
    path: ./demo-micro_service
    dependsOn: service-core
```

`dependsOn` ensures `service-core` deploys first — its Lambda Layer must exist before the microservice can attach to it, and its Glue ZIP must be in S3 before the Glue job can reference it.

### 2. service_core packages itself two ways

`service_core/serverless.yml` runs two build steps via `serverless-scriptable-plugin`:

```yaml
custom:
  scriptable:
    hooks:
      before:package:cleanup: >-
        node ../build-scripts/initialize.js layer ../service_core/layers/python/service_core/
        && node ../build-scripts/initialize.js glue-library ../service_core/glue/service_core/ 1.0.0
      after:deploy:finalize: >-
        aws s3 cp service_core_1.0.0.zip s3://ragu-blog-deployment/glueJobs/glue-libraries/ ...
```

The `initialize.js` script copies `service_core/repositories/` and `service_core/utils/` into both:

- `layers/python/service_core/` — staged for Lambda Layer publishing
- `glue/service_core/` — zipped as `service_core_1.0.0.zip`, uploaded to S3

### 3. Lambda consumes the Layer

```python
# demo-micro_service/lambdas/hello_world_lambda.py
from service_core.utils.logger import get_logger

logger = get_logger(__name__, service="hello-world")


def handler(event, context):
    logger.info(f"received event: {event}")
    return {"statusCode": 200, "body": "ok"}
```

Wired in `demo-micro_service/serverless.yml`:

```yaml
functions:
  hello-world:
    handler: lambdas/hello_world_lambda.handler
    layers:
      - ${cf:service-core-${self:provider.stage}.ServiceCoreLayersExport}
```

### 4. Glue consumes the ZIP

```python
# demo-micro_service/glue_jobs/hello_world_data_extractor.py
from service_core.utils.logger import get_logger

logger = get_logger(__name__, service=args["service_name"])
logger.info("Glue job starting")
```

Wired in the same `serverless.yml`:

```yaml
resources:
  Resources:
    HelloWorldGlueJob:
      Type: AWS::Glue::Job
      Properties:
        Command:
          Name: glueetl
          ScriptLocation: s3://.../glueJobs/scripts/hello_world_data_extractor.py
        DefaultArguments:
          "--extra-py-files": s3://.../glueJobs/glue-libraries/service_core_1.0.0.zip
          "--service-name": hello-world
```

Identical import path on both sides; different packaging mechanics. That's the whole pattern.

---

## Prerequisites

- Node.js >= 18, npm >= 8 (for Serverless Framework + scriptable plugin)
- Python 3.9 (matches the runtime configured in both `serverless.yml` files)
- AWS CLI configured with profiles named `dev`, `staging`, and/or `prod`
- An S3 deployment bucket (configured as `ragu-blog-deployment` in this repo — change to your own)
- IAM role configured with permissions for Lambda, Glue, S3, and CloudFormation

---

## Setup

```bash
npm install
```

Update the following placeholders for your environment before deploying:

| File | Placeholder | What to change it to |
|---|---|---|
| `service_core/serverless.yml` | `deploymentBucket: ragu-blog-deployment` | Your own S3 deployment bucket |
| `service_core/serverless.yml` | `role: arn:aws:iam::374053237961:role/Service-Apex` | Your service IAM role ARN |
| `demo-micro_service/serverless.yml` | Same two settings as above | Same values |
| `demo-micro_service/serverless.yml` | `custom.glueRole`, `custom.sharedLibsBucket`, `custom.glueScriptsBucket` | Your Glue role + buckets |

---

## Deploy

Deploy everything (compose walks the dependency graph and deploys in order):

```bash
npm run deploy:dev
# or: npm run deploy:staging  /  npm run deploy:prod
```

Deploy a single service:

```bash
serverless deploy --stage dev --config service_core/serverless.yml
serverless deploy --stage dev --config demo-micro_service/serverless.yml
```

After a successful deploy:

- The Lambda Layer is published with export name `ServiceUnderscorecoreUnderscorelayersLambdaLayer`
- The Glue library ZIP is at `s3://<bucket>/glueJobs/glue-libraries/service_core_1.0.0.zip`
- The `hello-world` Lambda is reachable at `GET /hello` on the deployed HTTP API
- The `hello-world-data-extractor` Glue job is registered (run it from the AWS Console or `aws glue start-job-run`)

---

## Tear down

```bash
npm run remove:dev
```

This destroys both services in reverse dependency order.

---

## Three principles this repo holds to

1. **Share and version reusable code.** Common utilities live in `service_core/`, versioned independently from consuming services.
2. **Package once, deploy multiple ways.** Same Python module → Lambda Layer for functions, ZIP for Glue jobs. No forks.
3. **One-way dependency flow.** Microservices depend on `service_core`; `service_core` never depends on consuming services.

---

## Related

- Article: [Structuring a Serverless Data Platform on AWS: A Reusable Blueprint for Lambda and Glue](https://raguvind.com/writing/aws-serverless-data-platform)
- Author: [Raguvind Tharanitharan](https://raguvind.com)

## License

MIT
