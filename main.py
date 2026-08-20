from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import yaml

from openapi_spec_validator import validate


app = FastAPI(
    title="OpenAPI Audit API",
    version="1.1.0",
    description="API de validation automatique de spécifications OpenAPI."
)


class ValidationRequest(BaseModel):
    specification: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "OpenAPI Audit API",
        "version": "1.1.0"
    }


def find_dr1_warnings(spec: dict[str, Any]) -> list[dict[str, str]]:
    warnings = []

    if not spec.get("servers"):
        warnings.append({
            "code": "DR1-SERVER",
            "message": "Aucun serveur n'est déclaré. Pour une Action GPT appelable, l'URL du serveur doit être connue."
        })

    operation_ids = set()

    paths = spec.get("paths", {})

    if isinstance(paths, dict):
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.lower() not in {
                    "get", "post", "put", "patch",
                    "delete", "options", "head", "trace"
                }:
                    continue

                if not isinstance(operation, dict):
                    continue

                operation_id = operation.get("operationId")

                if not operation_id:
                    warnings.append({
                        "code": "DR1-OPERATION-ID",
                        "message": f"{method.upper()} {path} ne possède pas d'operationId."
                    })
                elif operation_id in operation_ids:
                    warnings.append({
                        "code": "DR1-DUPLICATE-OPERATION-ID",
                        "message": f"L'operationId '{operation_id}' est utilisé plusieurs fois."
                    })
                else:
                    operation_ids.add(operation_id)

                if method.lower() in {"post", "put", "patch", "delete"}:
                    description = operation.get("description", "")

                    if not description:
                        warnings.append({
                            "code": "DR1-SIDE-EFFECT",
                            "message": (
                                f"{method.upper()} {path} peut avoir un effet externe, "
                                "mais aucune description n'est fournie."
                            )
                        })

    return warnings


@app.post("/validate")
def validate_openapi(request: ValidationRequest):
    errors = []
    warnings = []

    # Étape 1 : parsing YAML ou JSON
    try:
        specification = yaml.safe_load(request.specification)
    except yaml.YAMLError as exc:
        return {
            "valid": False,
            "syntaxValid": False,
            "openapiValid": False,
            "errors": [
                {
                    "type": "yaml",
                    "message": str(exc)
                }
            ],
            "warnings": []
        }

    if not isinstance(specification, dict):
        return {
            "valid": False,
            "syntaxValid": True,
            "openapiValid": False,
            "errors": [
                {
                    "type": "structure",
                    "message": "La spécification doit être un objet YAML ou JSON."
                }
            ],
            "warnings": []
        }

    # Étape 2 : validation OpenAPI automatique
    try:
        validate(specification)
        openapi_valid = True
    except Exception as exc:
        openapi_valid = False
        errors.append({
            "type": "openapi",
            "message": str(exc)
        })

    # Étape 3 : contrôles complémentaires DR1
    warnings.extend(find_dr1_warnings(specification))

    return {
        "valid": openapi_valid,
        "syntaxValid": True,
        "openapiValid": openapi_valid,
        "openapiVersion": specification.get("openapi"),
        "errors": errors,
        "warnings": warnings,
        "validation": {
            "yamlParsed": True,
            "automaticOpenAPIValidationExecuted": True,
            "realApiTestExecuted": False
        }
    }
