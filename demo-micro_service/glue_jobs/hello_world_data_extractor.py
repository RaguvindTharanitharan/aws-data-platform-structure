"""
Demo Glue job showing how to consume the same service_core module
that Lambda functions use — packaged this time as a ZIP and wired in
via the --extra-py-files Glue argument.

The import statement is identical to the Lambda's:

    from service_core.utils.logger import get_logger

This is the "one source, two packagings" pattern from the article.
The job code does not know whether it runs in Lambda or Glue; the
packaging is invisible at the import boundary.
"""

import sys

from awsglue.utils import getResolvedOptions  # type: ignore[import-not-found]

from service_core.utils.logger import get_logger

args = getResolvedOptions(sys.argv, ["service-name"])
logger = get_logger(__name__, service=args["service_name"])

logger.info("Glue job starting")
# ... extract / transform / load
logger.info("Glue job finished")
