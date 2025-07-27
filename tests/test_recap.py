import simplejson as json

from docketanalyzer import env, parse_docket_id


def test_recap_credentials():
    """Test that RECAP credentials are set in the environment variables."""
    key_check = bool(env.COURTLISTENER_TOKEN)
    assert key_check, "RECAP credentials are not set in the environment variables"


def test_recap_docket(sample_docket_id2):
    """Test RECAP docket."""
    from docketanalyzer.pacer import RecapAPI

    recap = RecapAPI(sleep=0.2)

    assert len(recap.docket_id_map) == 0, "Docket ID map should be empty"

    r = recap.dockets(sample_docket_id2)

    court, docket_number = parse_docket_id(sample_docket_id2)
    assert court in r.results[0]["court"], "Court should match the docket_id"
    assert r.results[0]["docket_number"] == docket_number, "Docket numbers should match"

    # Confirm inferred recap_id is saved
    assert len(recap.docket_id_map) == 1, "Docket ID map should not be empty"
    # Try again using inferred id
    r = recap.dockets(sample_docket_id2)
    results = json.dumps(r.results, indent=2)

    # Try one more time using recap_ids directly
    new_results = []
    for recap_id in recap.docket_id_map[sample_docket_id2]:
        r = recap.dockets(recap_id)
        new_results.extend(r.results)
    new_results = json.dumps(new_results, indent=2)
    assert results == new_results, "RECAP results do not match"


def test_recap_consolidated(index, sample_docket_id2):
    """Test RECAP consolidated docket."""
    from docketanalyzer.pacer import RecapAPI

    manager = index[sample_docket_id2]
    cached_results = manager.recap_path.read_text()
    recap = RecapAPI()
    r = recap.consolidated_docket(sample_docket_id2)
    results = json.dumps(r.results, indent=2)
    assert results == cached_results, "RECAP results do not match the cached results"
