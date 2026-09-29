import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import psycopg

from database import connect_db

router = APIRouter(tags=["health"])
logger = logging.getLogger("travel.health")


@router.get("/healthz")
def liveness() -> JSONResponse:
    return JSONResponse(
        {"status": "ok"}, headers={"Cache-Control": "no-store"}
    )


@router.get("/readyz")
def readiness() -> JSONResponse:
    try:
        with connect_db() as connection:
            connection.execute("SET LOCAL statement_timeout = '2s'")
            connection.execute("SELECT 1").fetchone()
    except psycopg.Error as exc:
        logger.warning("readiness_failed error_type=%s", type(exc).__name__)
        return JSONResponse(
            {"status": "unavailable"},
            status_code=503,
            headers={"Cache-Control": "no-store"},
        )
    return JSONResponse(
        {"status": "ready"}, headers={"Cache-Control": "no-store"}
    )