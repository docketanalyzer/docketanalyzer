import simplejson as json

from docketanalyzer import env, parse_docket_id
from docketanalyzer.pacer import RecapAPI


def test_recap_credentials():
    """Test that RECAP credentials are set in the environment variables."""
    key_check = bool(env.COURTLISTENER_TOKEN)
    assert key_check, "RECAP credentials are not set in the environment variables"


def test_recap_docket(sample_docket_id2, fixture_dir):
    """Test RECAP docket."""
    recap = RecapAPI(sleep=0.2)

    assert len(recap.docket_id_map) == 0, "Docket ID map should be empty"
    cached_results = (fixture_dir / "recap.docket.json").read_text()

    r = recap.dockets(sample_docket_id2)
    results = json.dumps(r.results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"

    court, docket_number = parse_docket_id(sample_docket_id2)
    assert court in r.results[0]["court"], "Court should match the docket_id"
    assert r.results[0]["docket_number"] == docket_number, "Docket numbers should match"

    # Confirm inferred recap_id is saved
    assert len(recap.docket_id_map) == 1, "Docket ID map should not be empty"
    # try again using inferred id
    r = recap.dockets(sample_docket_id2)
    results = json.dumps(r.results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"

    # try one more time using recap_ids directly
    results = []
    for recap_id in recap.docket_id_map[sample_docket_id2]:
        r = recap.dockets(recap_id)
        results.extend(r.results)
    results = json.dumps(results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"


def test_recap_entries(sample_docket_id2, fixture_dir):
    """Test RECAP entries."""
    recap = RecapAPI()
    cached_results = (fixture_dir / "recap.entries.json").read_text()
    r = recap.entries(sample_docket_id2)
    results = json.dumps(r.results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"


def test_recap_parties(sample_docket_id2, fixture_dir):
    """Test RECAP parties."""
    recap = RecapAPI()
    cached_results = (fixture_dir / "recap.parties.json").read_text()
    r = recap.parties(sample_docket_id2)
    results = json.dumps(r.results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"


def test_recap_attorneys(sample_docket_id2, fixture_dir):
    """Test RECAP attorneys."""
    recap = RecapAPI()
    cached_results = (fixture_dir / "recap.attorneys.json").read_text()
    r = recap.dockets(sample_docket_id2)
    results = json.dumps(r.results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"


def test_recap_consolidated(sample_docket_id2, fixture_dir):
    """Test RECAP consolidated docket."""
    recap = RecapAPI()
    cached_results = (fixture_dir / "recap.consolidated.json").read_text()
    r = recap.consolidated_docket(sample_docket_id2)
    results = json.dumps(r.results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"


"""
def test_recap_compare(sample_docket_id, sample_docket_json):
    ""Test RECAP consolidated compared to locally parsed.""
    recap = RecapAPI()
    r = recap.consolidated_docket(sample_docket_id)
    docket_json = r.results[0]

    logging.info(json.dumps(docket_json, indent=2))
    logging.info(json.dumps(sample_docket_json, indent=2))
    # Finish this and possibly adjust consolidated format
"""
