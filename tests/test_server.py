"""Unit tests for FastAPI Dashboard Backend Server."""

import pytest
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)


def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "protocol" in data


def test_api_scales():
    response = client.get("/api/scales")
    assert response.status_code == 200
    data = response.json()
    assert "scales" in data
    assert len(data["scales"]) >= 3


def test_api_routes():
    response = client.get("/api/routes?scale=25&page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert len(data["routes"]) > 0
    assert "prefix" in data["routes"][0]


def test_api_optimize():
    response = client.post("/api/optimize", json={"strategy": "HYBRID", "enabled": True})
    assert response.status_code == 200
    data = response.json()
    assert data["is_optimized"] is True
    assert data["reachability_preserved_pct"] == 100.0


def test_api_trace():
    response = client.post(
        "/api/trace",
        json={"src_as": 1, "dest_prefix": "10.0.0.0/24"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["delivered"] is True
    assert len(data["trace_steps"]) >= 1


def test_api_charts_and_report():
    res_charts = client.get("/api/charts")
    assert res_charts.status_code == 200
    assert len(res_charts.json()["charts"]) >= 3

    res_report = client.get("/api/report")
    assert res_report.status_code == 200
    assert "report_markdown" in res_report.json()


def test_api_prefixes():
    res_prefixes = client.get("/api/prefixes?scale=10")
    assert res_prefixes.status_code == 200
    data = res_prefixes.json()
    assert "prefixes" in data
    assert len(data["prefixes"]) > 0
    assert "prefix" in data["prefixes"][0]
    assert "origin_as" in data["prefixes"][0]
