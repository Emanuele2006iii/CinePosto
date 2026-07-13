"""Test di retry_request: retry con backoff, 403 non ritentato, propagazione errori."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from scraper.config import REQUEST_RETRY
from scraper.http import retry_request


def _mock_response(status_code: int) -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


# --- retry_request ---

def test_success_on_first_attempt():
    session = MagicMock()
    session.get.return_value = _mock_response(200)
    resp = retry_request("get", "http://example.com", session)
    assert resp.status_code == 200
    assert session.get.call_count == 1


def test_403_raises_immediately_without_retry():
    session = MagicMock()
    session.get.return_value = _mock_response(403)
    with pytest.raises(requests.HTTPError):
        retry_request("get", "http://example.com", session)
    assert session.get.call_count == 1


def test_500_retries_and_succeeds_on_second_attempt():
    session = MagicMock()
    session.get.side_effect = [_mock_response(500), _mock_response(200)]
    with patch("scraper.http.time.sleep"):
        resp = retry_request("get", "http://example.com", session)
    assert resp.status_code == 200
    assert session.get.call_count == 2


def test_exhausted_retries_raises_last_exception():
    session = MagicMock()
    session.get.return_value = _mock_response(500)
    with patch("scraper.http.time.sleep"):
        with pytest.raises(requests.HTTPError):
            retry_request("get", "http://example.com", session)
    assert session.get.call_count == REQUEST_RETRY


def test_network_error_retries_and_succeeds():
    session = MagicMock()
    session.get.side_effect = [
        requests.ConnectionError("connection reset"),
        requests.ConnectionError("connection reset"),
        _mock_response(200),
    ]
    with patch("scraper.http.time.sleep"):
        resp = retry_request("get", "http://example.com", session)
    assert resp.status_code == 200
    assert session.get.call_count == 3


def test_network_error_exhausted_retries_raises():
    session = MagicMock()
    session.get.side_effect = requests.ConnectionError("permanent failure")
    with patch("scraper.http.time.sleep"):
        with pytest.raises(requests.ConnectionError):
            retry_request("get", "http://example.com", session)
    assert session.get.call_count == REQUEST_RETRY


def test_kwargs_passed_to_session():
    session = MagicMock()
    session.post.return_value = _mock_response(200)
    retry_request("post", "http://example.com", session, json={"key": "val"})
    call_kwargs = session.post.call_args.kwargs
    assert call_kwargs.get("json") == {"key": "val"}
