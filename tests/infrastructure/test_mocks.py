from domain.enums import (
    AnalysisStatus,
    Provider,
    RecommendationAction,
    TyreCompound,
)
from domain.schemas import RaceEvent

from infrastructure.mocks import (
    MockGeminiProvider,
    MockGPTProvider,
)


def build_race_event() -> RaceEvent:
    return RaceEvent(
        circuit="Monaco",
        session="race",
        lap=20,
        driver="Test Driver",
        team="Test Team",
        position=5,
        event_type="strategic_opportunity",
        description="Strategic opportunity detected during the race.",
    )


def test_mock_gemini_returns_valid_analysis():
    provider = MockGeminiProvider()

    result = provider.analyze(build_race_event())

    assert result.provider == Provider.GEMINI
    assert result.model == "mock-gemini"
    assert result.status == AnalysisStatus.SUCCESS
    assert result.error is None


def test_mock_gpt_returns_valid_analysis():
    provider = MockGPTProvider()

    result = provider.analyze(build_race_event())

    assert result.provider == Provider.GPT
    assert result.model == "mock-gpt"
    assert result.status == AnalysisStatus.SUCCESS
    assert result.error is None


def test_mock_providers_return_strategic_recommendations():
    race_event = build_race_event()

    gemini_result = MockGeminiProvider().analyze(race_event)
    gpt_result = MockGPTProvider().analyze(race_event)

    assert (
        gemini_result.recommendation.action
        == RecommendationAction.PIT_STOP
    )

    assert (
        gpt_result.recommendation.action
        == RecommendationAction.PIT_STOP
    )

    assert (
        gemini_result.recommendation.tyre_compound
        == TyreCompound.MEDIUM
    )

    assert (
        gpt_result.recommendation.tyre_compound
        == TyreCompound.MEDIUM
    )


def test_mock_providers_agree_on_target_lap():
    race_event = build_race_event()

    gemini_result = MockGeminiProvider().analyze(race_event)
    gpt_result = MockGPTProvider().analyze(race_event)

    assert gemini_result.recommendation.target_lap == 20
    assert gpt_result.recommendation.target_lap == 20


def test_mock_providers_have_sufficient_confidence():
    race_event = build_race_event()

    gemini_result = MockGeminiProvider().analyze(race_event)
    gpt_result = MockGPTProvider().analyze(race_event)

    assert gemini_result.confidence >= 0.80
    assert gpt_result.confidence >= 0.80

    assert gemini_result.recommendation.confidence >= 0.80
    assert gpt_result.recommendation.confidence >= 0.80


def test_mock_provider_metrics_are_consistent():
    race_event = build_race_event()

    gemini_result = MockGeminiProvider().analyze(race_event)
    gpt_result = MockGPTProvider().analyze(race_event)

    for result in (gemini_result, gpt_result):
        assert (
            result.metrics.total_tokens
            == result.metrics.input_tokens
            + result.metrics.output_tokens
        )

        assert result.metrics.latency_ms >= 0
        assert result.metrics.cost >= 0
        assert result.metrics.retries >= 0