import pytest

from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.synthesize import LLMSynthesizer


@pytest.fixture
def sample_results():
    chunk1 = CorpusChunk(
        work="Brihat Parashara Hora Shastra",
        chapter="12",
        verse="5",
        text="Jupiter in the 1st house confers high intellect, noble character, and profound wisdom.",
        source_file="bphs.txt",
        char_start=0,
        char_end=80,
        tier="verse",
    )
    chunk2 = CorpusChunk(
        work="Phaladeepika",
        chapter="8",
        verse="14",
        text="When Jupiter occupies the Lagna, the native will be handsome, virtuous, and long-lived.",
        source_file="phaladeepika.txt",
        char_start=81,
        char_end=170,
        tier="verse",
    )
    return [SearchResult(chunk=chunk1, score=0.95), SearchResult(chunk=chunk2, score=0.88)]

def test_synthesizer_stream_offline_graceful_fallback(sample_results):
    # Point to dead port
    synth = LLMSynthesizer(
        provider="openai",
        model="nakshatra-combo",
        base_url="http://127.0.0.1:59999/v1",
        api_key="sk-test",
    )
    tokens = list(synth.synthesize_stream("What does Jupiter in 1st house do?", sample_results))
    full_output = "".join(tokens)
    assert len(tokens) > 0
    assert "Notice:" in full_output or "Jupiter in the 1st house" in full_output
    assert "Brihat Parashara Hora Shastra" in full_output

def test_synthesizer_complete_offline_graceful_fallback(sample_results):
    synth = LLMSynthesizer(
        provider="openai",
        model="nakshatra-combo",
        base_url="http://127.0.0.1:59999/v1",
        api_key="sk-test",
    )
    ans = synth.synthesize("What does Jupiter in 1st house do?", sample_results)
    assert ans is not None
    assert "Notice:" in ans.answer
    assert "Brihat Parashara Hora Shastra" in ans.answer
    assert len(ans.citations) > 0
