/* ============================================================
   ARXIA DASHBOARD
   Navigation + Race Control
   ============================================================ */


/* ============================================================
   MODULE DEFINITIONS
   ============================================================ */

const modules = {

    overview: {
        number: "01",
        section: "RACE CONTROL",
        title: "ARXIA RACE CONTROL",
        description: "What is happening right now?",
        icon: "🏁"
    },

    timeline: {
        number: "02",
        section: "RACE TIMELINE",
        title: "RACE TIMELINE",
        description: "How did the race context evolve?",
        icon: "🏎️"
    },

    analysis: {
        number: "03",
        section: "AI INTELLIGENCE",
        title: "AI ANALYSIS",
        description: "What does each model think?",
        icon: "🧠"
    },

    comparison: {
        number: "04",
        section: "MODEL COMPARISON",
        title: "MODEL COMPARISON",
        description: "How much do the models agree?",
        icon: "⚖️"
    },

    risk: {
        number: "05",
        section: "RISK ENGINE",
        title: "RISK ENGINE",
        description: "What is the risk of automation?",
        icon: "⚠️"
    },

    decision: {
        number: "06",
        section: "ARXIA DECISION",
        title: "WHAT DID ARXIA DECIDE?",
        description: "The final system decision.",
        icon: "🎯"
    },

    review: {
        number: "07",
        section: "HUMAN REVIEW",
        title: "HUMAN REVIEW",
        description: "Does an engineer need to intervene?",
        icon: "👤"
    },

    metrics: {
        number: "08",
        section: "SYSTEM TELEMETRY",
        title: "SYSTEM METRICS",
        description: "How did the decision system perform?",
        icon: "📊"
    }

};


/* ============================================================
   SIMULATED RACE DATA
   ============================================================ */

const raceState = {

    lap: 42,
    totalLaps: 67,

    position: 4,
    gap: "+3.821 s",

    speed: 287,

    tyres: "MEDIUM",
    tyreAge: 18,

    fuel: 18.4,

    tyreTemp: 91,
    engineTemp: 104,

    ers: 72,

    trackStatus: "GREEN",

    raceSituation: {

        title: "NORMAL RACE CONDITIONS",

        description:
            "Track conditions are stable. ARXIA is monitoring the current race state."

    },

    aiSignal: {

        status: "MONITORING",

        confidence: 78,

        description:
            "Models are evaluating pace, tyre degradation and strategic conditions."

    },

    decision: {

        action: "MONITOR",

        confidence: 82,

        description:
            "No immediate intervention required."

    }

};


/* ============================================================
   DOM REFERENCES
   ============================================================ */

const navItems =
    document.querySelectorAll(".nav-item");

const pageTitle =
    document.getElementById("page-title");

const pageDescription =
    document.getElementById("page-description");

const moduleContainer =
    document.getElementById("module-container");

const eyebrow =
    document.querySelector(".eyebrow");

const systemTime =
    document.getElementById("system-time");


/* ============================================================
   OVERVIEW MODULE
   ============================================================ */

function renderOverview() {

    moduleContainer.innerHTML = `

        <div class="overview-grid">


            <!-- =================================================
                 RACE STATUS
                 ================================================= -->

            <section class="dashboard-card race-status-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            RACE STATUS
                        </span>

                        <h2>
                            LIVE RACE
                        </h2>

                    </div>

                    <span class="card-icon">
                        🏁
                    </span>

                </div>


                <div class="race-lap">

                    <span class="metric-label">
                        CURRENT LAP
                    </span>

                    <div class="lap-value">

                        <strong>
                            ${raceState.lap}
                        </strong>

                        <span>
                            / ${raceState.totalLaps}
                        </span>

                    </div>

                </div>


                <div class="metrics-row">

                    <div class="metric">

                        <span class="metric-label">
                            POSITION
                        </span>

                        <strong>
                            P${raceState.position}
                        </strong>

                    </div>


                    <div class="metric">

                        <span class="metric-label">
                            GAP
                        </span>

                        <strong>
                            ${raceState.gap}
                        </strong>

                    </div>

                </div>

            </section>


            <!-- =================================================
                 CAR STATE / TELEMETRY
                 ================================================= -->

            <section class="dashboard-card car-state-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            CAR STATE
                        </span>

                        <h2>
                            TELEMETRY
                        </h2>

                    </div>

                    <span class="card-icon">
                        🏎️
                    </span>

                </div>


                <div class="telemetry-primary">

                    <div class="telemetry-speed">

                        <span class="metric-label">
                            CURRENT SPEED
                        </span>

                        <div class="telemetry-speed-value">

                            <strong>
                                ${raceState.speed}
                            </strong>

                            <span>
                                KM/H
                            </span>

                        </div>

                    </div>


                    <div class="telemetry-speed-meta">

                        <span>
                            LIVE TELEMETRY
                        </span>

                        <div class="telemetry-live-dot"></div>

                    </div>

                </div>


                <div class="telemetry-data-grid">


                    <!-- TYRES -->

                    <div class="telemetry-data">

                        <div class="telemetry-data-top">

                            <span class="metric-label">
                                TYRES
                            </span>

                            <span class="telemetry-status">
                                ACTIVE
                            </span>

                        </div>

                        <strong class="telemetry-tyre">
                            ${raceState.tyres}
                        </strong>

                        <span class="telemetry-sub">
                            ${raceState.tyreAge} LAPS
                        </span>

                    </div>


                    <!-- FUEL -->

                    <div class="telemetry-data">

                        <div class="telemetry-data-top">

                            <span class="metric-label">
                                FUEL
                            </span>

                            <strong>
                                ${raceState.fuel}
                                <small>L</small>
                            </strong>

                        </div>

                        <div class="telemetry-progress">

                            <span
                                style="width: ${Math.min(
                                    (raceState.fuel / 110) * 100,
                                    100
                                )}%"
                            ></span>

                        </div>

                        <span class="telemetry-sub">
                            EST. REMAINING
                        </span>

                    </div>


                    <!-- ERS -->

                    <div class="telemetry-data">

                        <div class="telemetry-data-top">

                            <span class="metric-label">
                                ERS
                            </span>

                            <strong>
                                ${raceState.ers}
                                <small>%</small>
                            </strong>

                        </div>

                        <div class="telemetry-progress">

                            <span
                                style="width: ${raceState.ers}%"
                            ></span>

                        </div>

                        <span class="telemetry-sub">
                            ENERGY AVAILABLE
                        </span>

                    </div>


                </div>

            </section>


            <!-- =================================================
                 RACE SITUATION
                 ================================================= -->

            <section class="dashboard-card situation-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            RACE SITUATION
                        </span>

                        <h2>
                            ${raceState.raceSituation.title}
                        </h2>

                    </div>

                    <div class="state-indicator">

                        <span></span>

                        ${raceState.trackStatus}

                    </div>

                </div>


                <div class="situation-summary">

                    <div class="situation-status-line">

                        <span class="situation-status-dot"></span>

                        <span>
                            TRACK CONDITIONS STABLE
                        </span>

                    </div>


                    <p class="card-description">
                        ${raceState.raceSituation.description}
                    </p>

                </div>


                <div class="situation-data">


                    <!-- TYRE TEMP -->

                    <div class="situation-metric">

                        <div class="situation-metric-header">

                            <span class="metric-label">
                                TYRE TEMP
                            </span>

                            <span class="situation-metric-state">
                                NOMINAL
                            </span>

                        </div>


                        <div class="situation-metric-value">

                            <strong>
                                ${raceState.tyreTemp}
                            </strong>

                            <span>
                                °C
                            </span>

                        </div>


                        <div class="situation-scale">

                            <span
                                style="width: ${Math.min(
                                    (raceState.tyreTemp / 120) * 100,
                                    100
                                )}%"
                            ></span>

                        </div>

                    </div>


                    <!-- ENGINE TEMP -->

                    <div class="situation-metric">

                        <div class="situation-metric-header">

                            <span class="metric-label">
                                ENGINE TEMP
                            </span>

                            <span class="situation-metric-state">
                                NOMINAL
                            </span>

                        </div>


                        <div class="situation-metric-value">

                            <strong>
                                ${raceState.engineTemp}
                            </strong>

                            <span>
                                °C
                            </span>

                        </div>


                        <div class="situation-scale">

                            <span
                                style="width: ${Math.min(
                                    (raceState.engineTemp / 130) * 100,
                                    100
                                )}%"
                            ></span>

                        </div>

                    </div>


                </div>

            </section>


            <!-- =================================================
                 AI SIGNAL
                 ================================================= -->

            <section class="dashboard-card ai-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            AI SIGNAL
                        </span>

                        <h2>
                            ${raceState.aiSignal.status}
                        </h2>

                    </div>

                    <div class="ai-status-indicator">

                        <span></span>

                        ACTIVE

                    </div>

                </div>


                <div class="ai-confidence-main">

                    <div class="ai-confidence-label">

                        <span class="metric-label">
                            AGGREGATED MODEL CONFIDENCE
                        </span>

                        <strong>
                            ${raceState.aiSignal.confidence}%
                        </strong>

                    </div>


                    <div class="ai-confidence-bar">

                        <span
                            style="width: ${raceState.aiSignal.confidence}%"
                        ></span>

                    </div>

                </div>


                <div class="ai-model-grid">


                    <!-- PACE MODEL -->

                    <div class="ai-model">

                        <div class="ai-model-header">

                            <span>
                                PACE MODEL
                            </span>

                            <strong>
                                81%
                            </strong>

                        </div>

                        <div class="ai-model-bar">

                            <span style="width: 81%"></span>

                        </div>

                    </div>


                    <!-- TYRE MODEL -->

                    <div class="ai-model">

                        <div class="ai-model-header">

                            <span>
                                TYRE MODEL
                            </span>

                            <strong>
                                76%
                            </strong>

                        </div>

                        <div class="ai-model-bar">

                            <span style="width: 76%"></span>

                        </div>

                    </div>


                    <!-- STRATEGY MODEL -->

                    <div class="ai-model">

                        <div class="ai-model-header">

                            <span>
                                STRATEGY MODEL
                            </span>

                            <strong>
                                79%
                            </strong>

                        </div>

                        <div class="ai-model-bar">

                            <span style="width: 79%"></span>

                        </div>

                    </div>


                </div>


                <div class="ai-interpretation">

                    <span class="ai-interpretation-label">
                        SYSTEM INTERPRETATION
                    </span>

                    <p>
                        ${raceState.aiSignal.description}
                    </p>

                </div>

            </section>


            <!-- =================================================
                 ARXIA DECISION
                 ================================================= -->

            <section class="dashboard-card decision-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            ARXIA DECISION
                        </span>

                        <h2>
                            ${raceState.decision.action}
                        </h2>

                    </div>

                    <span class="decision-icon">
                        🎯
                    </span>

                </div>


                <div class="decision-hero">

                    <span class="decision-hero-label">
                        SYSTEM RECOMMENDATION
                    </span>

                    <div class="decision-action">
                        ${raceState.decision.action}
                    </div>

                    <p>
                        ${raceState.decision.description}
                    </p>

                </div>


                <div class="decision-confidence-block">

                    <div class="decision-confidence-header">

                        <div>

                            <span class="metric-label">
                                DECISION CONFIDENCE
                            </span>

                            <span class="decision-confidence-sub">
                                ARXIA DECISION CORE
                            </span>

                        </div>

                        <strong>
                            ${raceState.decision.confidence}%
                        </strong>

                    </div>


                    <div class="decision-confidence-track">

                        <div
                            class="decision-confidence-fill"
                            style="width: ${raceState.decision.confidence}%"
                        ></div>

                    </div>

                </div>


                <div class="decision-logic">

                    <div class="decision-logic-header">

                        <span class="metric-label">
                            DECISION PIPELINE
                        </span>

                        <span>
                            REAL-TIME
                        </span>

                    </div>


                    <div class="decision-flow">


                        <div class="decision-node">

                            <span class="decision-node-icon">
                                🧠
                            </span>

                            <div>

                                <strong>
                                    AI SIGNAL
                                </strong>

                                <small>
                                    78% CONFIDENCE
                                </small>

                            </div>

                        </div>


                        <div class="decision-connector"></div>


                        <div class="decision-node">

                            <span class="decision-node-icon">
                                ⚠️
                            </span>

                            <div>

                                <strong>
                                    RISK ENGINE
                                </strong>

                                <small>
                                    LOW RISK
                                </small>

                            </div>

                        </div>


                        <div class="decision-connector"></div>


                        <div class="decision-node decision-node-final">

                            <span class="decision-node-icon">
                                🎯
                            </span>

                            <div>

                                <strong>
                                    ARXIA
                                </strong>

                                <small>
                                    ${raceState.decision.action}
                                </small>

                            </div>

                        </div>


                    </div>

                </div>

            </section>


        </div>

    `;
}


/* ============================================================
   RACE TIMELINE MODULE
   ============================================================ */

function renderTimeline() {

    moduleContainer.innerHTML = `

        <div class="timeline-module">

            <div class="timeline-header">

                <div>
                    <span class="card-kicker">
                        RACE TIMELINE
                    </span>

                    <h2>
                        How did the race context evolve?
                    </h2>
                </div>

                <div class="timeline-live">
                    <span></span>
                    LIVE
                </div>

            </div>


            <div class="timeline-summary">

                <section class="dashboard-card timeline-stat">

                    <span class="metric-label">
                        CURRENT LAP
                    </span>

                    <div class="timeline-stat-value">
                        <strong>
                            ${raceState.lap}
                        </strong>

                        <span>
                            / ${raceState.totalLaps}
                        </span>
                    </div>

                </section>


                <section class="dashboard-card timeline-stat">

                    <span class="metric-label">
                        SESSION TIME
                    </span>

                    <div class="timeline-session-time">
                        01:24:36
                    </div>

                </section>

            </div>


            <section class="dashboard-card timeline-progress-card">

                <div class="card-header">

                    <div>
                        <span class="card-kicker">
                            RACE PROGRESS
                        </span>
                    </div>

                </div>


                <div class="race-progress">

                    <div class="race-progress-line"></div>

                    <div class="race-progress-point start">
                        <span></span>
                        <small>START</small>
                    </div>

                    <div class="race-progress-point">
                        <span></span>
                        <small>S1</small>
                    </div>

                    <div class="race-progress-point">
                        <span></span>
                        <small>S2</small>
                    </div>

                    <div class="race-progress-point">
                        <span></span>
                        <small>S3</small>
                    </div>

                    <div class="race-progress-point current">
                        <span></span>
                        <small>NOW</small>
                    </div>

                </div>

            </section>


            <section class="dashboard-card timeline-events-card">

                <div class="card-header">

                    <div>
                        <span class="card-kicker">
                            RECENT RACE EVENTS
                        </span>
                    </div>

                </div>


                <div class="timeline-events">

                    <div class="timeline-event current">

                        <span class="timeline-event-lap">
                            LAP 42
                        </span>

                        <span>
                            SECTOR 3
                        </span>

                        <strong>
                            +0.18 s
                        </strong>

                        <span class="timeline-event-status">
                            CURRENT
                        </span>

                    </div>


                    <div class="timeline-event">

                        <span class="timeline-event-lap">
                            LAP 41
                        </span>

                        <span>
                            SECTOR 2
                        </span>

                        <strong>
                            +0.04 s
                        </strong>

                        <span class="timeline-event-status">
                            STABLE
                        </span>

                    </div>


                    <div class="timeline-event">

                        <span class="timeline-event-lap">
                            LAP 40
                        </span>

                        <span>
                            TYRE STATE
                        </span>

                        <strong>
                            MEDIUM
                        </strong>

                        <span class="timeline-event-status">
                            MONITOR
                        </span>

                    </div>


                    <div class="timeline-event">

                        <span class="timeline-event-lap">
                            LAP 39
                        </span>

                        <span>
                            AI SIGNAL
                        </span>

                        <strong>
                            78%
                        </strong>

                        <span class="timeline-event-status">
                            UPDATED
                        </span>

                    </div>

                </div>

            </section>

        </div>

    `;
}


/* ============================================================
   AI ANALYSIS MODULE
   ============================================================ */

function renderAnalysis() {

    moduleContainer.innerHTML = `

        <div class="analysis-module">


            <!-- =================================================
                 ANALYSIS HEADER
                 ================================================= -->

            <div class="analysis-header">

                <div>

                    <span class="card-kicker">
                        AI ANALYSIS
                    </span>

                    <h2>
                        What does each model think?
                    </h2>

                </div>


                <div class="analysis-live">

                    <span></span>

                    LIVE

                </div>

            </div>


            <!-- =================================================
                 ANALYSIS SUMMARY
                 ================================================= -->

            <div class="analysis-summary">


                <section class="dashboard-card analysis-stat">

                    <span class="metric-label">
                        AGGREGATED SIGNAL
                    </span>


                    <div class="analysis-stat-value">

                        <strong>
                            ${raceState.aiSignal.confidence}%
                        </strong>

                    </div>


                    <span class="analysis-stat-status">
                        CONFIDENCE
                    </span>

                </section>


                <section class="dashboard-card analysis-stat">

                    <span class="metric-label">
                        MODEL AGREEMENT
                    </span>


                    <div class="analysis-stat-value">

                        <strong>
                            82%
                        </strong>

                    </div>


                    <span class="analysis-stat-status">
                        HIGH
                    </span>

                </section>


            </div>


            <!-- =================================================
                 MODEL SIGNALS
                 ================================================= -->

            <section class="dashboard-card analysis-models-card">


                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            MODEL SIGNALS
                        </span>

                    </div>

                </div>


                <div class="analysis-models">


                    <!-- PACE MODEL -->

                    <div class="analysis-model">

                        <div class="analysis-model-icon">
                            🧠
                        </div>


                        <div class="analysis-model-content">

                            <div class="analysis-model-header">

                                <div>

                                    <strong>
                                        PACE MODEL
                                    </strong>

                                    <span>
                                        Race pace remains stable
                                    </span>

                                </div>


                                <strong class="analysis-model-value">
                                    81%
                                </strong>

                            </div>


                            <div class="analysis-model-bar">

                                <span
                                    style="width: 81%"
                                ></span>

                            </div>

                        </div>

                    </div>


                    <!-- TYRE MODEL -->

                    <div class="analysis-model">

                        <div class="analysis-model-icon">
                            🛞
                        </div>


                        <div class="analysis-model-content">

                            <div class="analysis-model-header">

                                <div>

                                    <strong>
                                        TYRE MODEL
                                    </strong>

                                    <span>
                                        Medium degradation is moderate
                                    </span>

                                </div>


                                <strong class="analysis-model-value">
                                    76%
                                </strong>

                            </div>


                            <div class="analysis-model-bar">

                                <span
                                    style="width: 76%"
                                ></span>

                            </div>

                        </div>

                    </div>


                    <!-- STRATEGY MODEL -->

                    <div class="analysis-model">

                        <div class="analysis-model-icon">
                            🎯
                        </div>


                        <div class="analysis-model-content">

                            <div class="analysis-model-header">

                                <div>

                                    <strong>
                                        STRATEGY MODEL
                                    </strong>

                                    <span>
                                        No strategic intervention required
                                    </span>

                                </div>


                                <strong class="analysis-model-value">
                                    79%
                                </strong>

                            </div>


                            <div class="analysis-model-bar">

                                <span
                                    style="width: 79%"
                                ></span>

                            </div>

                        </div>

                    </div>


                </div>


            </section>


            <!-- =================================================
                 AI INTERPRETATION
                 ================================================= -->

            <section class="dashboard-card analysis-interpretation-card">


                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            AI INTERPRETATION
                        </span>

                    </div>


                    <div class="analysis-interpretation-status">

                        <span></span>

                        ACTIVE

                    </div>

                </div>


                <div class="analysis-interpretation">

                    <p>
                        ${raceState.aiSignal.description}
                    </p>

                </div>


            </section>


        </div>

    `;
}


/* ============================================================
   MODEL COMPARISON MODULE
   ============================================================ */

function renderComparison() {

    moduleContainer.innerHTML = `

        <div class="comparison-module">


            <!-- =================================================
                 COMPARISON HEADER
                 ================================================= -->

            <div class="comparison-header">

                <div>

                    <span class="card-kicker">
                        MODEL COMPARISON
                    </span>

                    <h2>
                        How much do the models agree?
                    </h2>

                </div>


                <div class="comparison-live">

                    <span></span>

                    LIVE

                </div>

            </div>


            <!-- =================================================
                 COMPARISON SUMMARY
                 ================================================= -->

            <div class="comparison-summary">


                <section class="dashboard-card comparison-stat">

                    <span class="metric-label">
                        MODEL AGREEMENT
                    </span>


                    <div class="comparison-stat-value">

                        <strong>
                            82%
                        </strong>

                    </div>


                    <span class="comparison-stat-status">
                        HIGH
                    </span>

                </section>


                <section class="dashboard-card comparison-stat">

                    <span class="metric-label">
                        SIGNAL SPREAD
                    </span>


                    <div class="comparison-stat-value">

                        <strong>
                            5 pts
                        </strong>

                    </div>


                    <span class="comparison-stat-status">
                        LOW
                    </span>

                </section>


            </div>


            <!-- =================================================
                 MODEL CONSENSUS
                 ================================================= -->

            <section class="dashboard-card comparison-consensus-card">


                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            MODEL CONSENSUS
                        </span>

                    </div>

                </div>


                <div class="comparison-table">


                    <div class="comparison-table-header">

                        <span></span>

                        <span>
                            PACE
                        </span>

                        <span>
                            TYRE
                        </span>

                        <span>
                            STRATEGY
                        </span>

                    </div>


                    <div class="comparison-table-row">

                        <strong>
                            AI MODEL
                        </strong>


                        <span>
                            81%
                        </span>


                        <span>
                            76%
                        </span>


                        <span>
                            79%
                        </span>

                    </div>


                    <div class="comparison-bars">

                        <div class="comparison-bar-column">

                            <div class="comparison-point"
                                 style="bottom: 81%">
                            </div>

                            <div class="comparison-bar-line">

                                <span
                                    style="height: 81%"
                                ></span>

                            </div>

                        </div>


                        <div class="comparison-bar-column">

                            <div class="comparison-point"
                                 style="bottom: 76%">
                            </div>

                            <div class="comparison-bar-line">

                                <span
                                    style="height: 76%"
                                ></span>

                            </div>

                        </div>


                        <div class="comparison-bar-column">

                            <div class="comparison-point"
                                 style="bottom: 79%"
                            ></div>

                            <div class="comparison-bar-line">

                                <span
                                    style="height: 79%"
                                ></span>

                            </div>

                        </div>

                    </div>


                </div>


            </section>


            <!-- =================================================
                 SIGNAL INTERPRETATION
                 ================================================= -->

            <section class="dashboard-card comparison-interpretation-card">


                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            SIGNAL INTERPRETATION
                        </span>

                    </div>


                    <div class="comparison-status">

                        <span></span>

                        CONSISTENT

                    </div>

                </div>


                <div class="comparison-interpretation">

                    <p>
                        Models remain closely aligned. No significant
                        disagreement detected across pace, tyre and
                        strategy signals.
                    </p>

                </div>


            </section>


        </div>

    `;
}


/* ============================================================
   RISK ENGINE MODULE
   ============================================================ */

function renderRisk() {

    moduleContainer.innerHTML = `

        <div class="risk-module">


            <!-- =================================================
                 RISK HEADER
                 ================================================= -->

            <div class="risk-header">

                <div>

                    <span class="card-kicker">
                        RISK ENGINE
                    </span>

                    <h2>
                        What is the risk of automation?
                    </h2>

                </div>


                <div class="risk-live">

                    <span></span>

                    REAL-TIME

                </div>

            </div>


            <!-- =================================================
                 RISK OVERVIEW
                 ================================================= -->

            <div class="risk-overview">


                <section class="dashboard-card risk-level-card">

                    <span class="metric-label">
                        CURRENT RISK
                    </span>


                    <div class="risk-level">

                        <strong>
                            LOW
                        </strong>

                        <span>
                            RISK LEVEL
                        </span>

                    </div>


                    <div class="risk-meter">

                        <span
                            style="width: 28%"
                        ></span>

                    </div>


                    <p class="risk-description">
                        Current race conditions present limited
                        automation risk.
                    </p>

                </section>


                <section class="dashboard-card risk-score-card">

                    <span class="metric-label">
                        RISK SCORE
                    </span>


                    <div class="risk-score">

                        <strong>
                            28
                        </strong>

                        <span>
                            / 100
                        </span>

                    </div>


                    <span class="risk-score-state">
                        WITHIN SAFE OPERATING RANGE
                    </span>

                </section>

            </div>


            <!-- =================================================
                 RISK FACTORS
                 ================================================= -->

            <section class="dashboard-card risk-factors-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            RISK FACTORS
                        </span>

                        <h2>
                            SYSTEM CONDITIONS
                        </h2>

                    </div>

                </div>


                <div class="risk-factors">


                    <div class="risk-factor">

                        <div class="risk-factor-header">

                            <span>
                                TYRE DEGRADATION
                            </span>

                            <strong>
                                LOW
                            </strong>

                        </div>


                        <div class="risk-factor-bar">

                            <span
                                style="width: 24%"
                            ></span>

                        </div>

                    </div>


                    <div class="risk-factor">

                        <div class="risk-factor-header">

                            <span>
                                TRACK CONDITIONS
                            </span>

                            <strong>
                                LOW
                            </strong>

                        </div>


                        <div class="risk-factor-bar">

                            <span
                                style="width: 18%"
                            ></span>

                        </div>

                    </div>


                    <div class="risk-factor">

                        <div class="risk-factor-header">

                            <span>
                                MODEL UNCERTAINTY
                            </span>

                            <strong>
                                MODERATE
                            </strong>

                        </div>


                        <div class="risk-factor-bar">

                            <span
                                style="width: 42%"
                            ></span>

                        </div>

                    </div>


                    <div class="risk-factor">

                        <div class="risk-factor-header">

                            <span>
                                STRATEGIC COMPLEXITY
                            </span>

                            <strong>
                                LOW
                            </strong>

                        </div>


                        <div class="risk-factor-bar">

                            <span
                                style="width: 31%"
                            ></span>

                        </div>

                    </div>


                </div>

            </section>


            <!-- =================================================
                 RISK INTERPRETATION
                 ================================================= -->

            <section class="dashboard-card risk-interpretation-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            RISK ASSESSMENT
                        </span>

                    </div>


                    <div class="risk-status">

                        <span></span>

                        STABLE

                    </div>

                </div>


                <div class="risk-assessment">

                    <p>
                        Current signals do not indicate a need
                        for intervention. ARXIA can continue
                        monitoring the race state.
                    </p>

                </div>

            </section>


        </div>

    `;
}


/* ============================================================
   ARXIA DECISION MODULE
   ============================================================ */

function renderDecision() {

    moduleContainer.innerHTML = `

        <div class="decision-module">


            <!-- =================================================
                 DECISION HEADER
                 ================================================= -->

            <div class="decision-module-header">

                <div>

                    <span class="card-kicker">
                        ARXIA DECISION
                    </span>

                    <h2>
                        What did ARXIA decide?
                    </h2>

                </div>


                <div class="decision-live">

                    <span></span>

                    LIVE

                </div>

            </div>


            <!-- =================================================
                 DECISION HERO
                 ================================================= -->

            <section class="dashboard-card decision-main-card">

                <div class="decision-main-top">

                    <div>

                        <span class="metric-label">
                            FINAL SYSTEM DECISION
                        </span>

                        <div class="decision-main-action">
                            ${raceState.decision.action}
                        </div>

                    </div>


                    <div class="decision-main-icon">
                        🎯
                    </div>

                </div>


                <div class="decision-main-description">

                    <p>
                        ${raceState.decision.description}
                    </p>

                </div>


                <div class="decision-main-confidence">

                    <div class="decision-confidence-header">

                        <div>

                            <span class="metric-label">
                                DECISION CONFIDENCE
                            </span>

                            <span class="decision-confidence-sub">
                                ARXIA DECISION CORE
                            </span>

                        </div>

                        <strong>
                            ${raceState.decision.confidence}%
                        </strong>

                    </div>


                    <div class="decision-confidence-track">

                        <div
                            class="decision-confidence-fill"
                            style="width: ${raceState.decision.confidence}%"
                        ></div>

                    </div>

                </div>

            </section>


            <!-- =================================================
                 DECISION FACTORS
                 ================================================= -->

            <section class="dashboard-card decision-factors-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            DECISION FACTORS
                        </span>

                        <h2>
                            SYSTEM INPUTS
                        </h2>

                    </div>

                </div>


                <div class="decision-factors">


                    <div class="decision-factor">

                        <div class="decision-factor-icon">
                            🧠
                        </div>

                        <div class="decision-factor-content">

                            <div class="decision-factor-header">

                                <span>
                                    AI SIGNAL
                                </span>

                                <strong>
                                    78%
                                </strong>

                            </div>

                            <p>
                                Models remain aligned with current
                                race conditions.
                            </p>

                        </div>

                    </div>


                    <div class="decision-factor">

                        <div class="decision-factor-icon">
                            ⚠️
                        </div>

                        <div class="decision-factor-content">

                            <div class="decision-factor-header">

                                <span>
                                    RISK ENGINE
                                </span>

                                <strong>
                                    LOW RISK
                                </strong>

                            </div>

                            <p>
                                No critical automation risk detected.
                            </p>

                        </div>

                    </div>


                    <div class="decision-factor">

                        <div class="decision-factor-icon">
                            🏎️
                        </div>

                        <div class="decision-factor-content">

                            <div class="decision-factor-header">

                                <span>
                                    RACE CONTEXT
                                </span>

                                <strong>
                                    STABLE
                                </strong>

                            </div>

                            <p>
                                Track and vehicle conditions remain
                                within expected parameters.
                            </p>

                        </div>

                    </div>


                </div>

            </section>


            <!-- =================================================
                 DECISION INTERPRETATION
                 ================================================= -->

            <section class="dashboard-card decision-interpretation-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            DECISION INTERPRETATION
                        </span>

                    </div>


                    <div class="decision-status">

                        <span></span>

                        MONITORING

                    </div>

                </div>


                <div class="decision-interpretation">

                    <p>
                        ARXIA recommends continued monitoring.
                        Current race conditions do not justify
                        immediate intervention.
                    </p>

                </div>

            </section>


        </div>

    `;
}


/* ============================================================
   HUMAN REVIEW MODULE
   ============================================================ */

function renderReview() {

    moduleContainer.innerHTML = `

        <div class="review-module">


            <!-- =================================================
                 REVIEW HEADER
                 ================================================= -->

            <div class="review-module-header">

                <div>

                    <span class="card-kicker">
                        HUMAN REVIEW
                    </span>

                    <h2>
                        Does an engineer need to intervene?
                    </h2>

                </div>


                <div class="review-live">

                    <span></span>

                    LIVE

                </div>

            </div>


            <!-- =================================================
                 REVIEW STATUS
                 ================================================= -->

            <section class="dashboard-card review-status-card">

                <div class="review-status-main">

                    <div class="review-status-indicator">

                        <span></span>

                    </div>


                    <div class="review-status-content">

                        <span class="metric-label">
                            REVIEW STATUS
                        </span>

                        <h2>
                            NO INTERVENTION REQUIRED
                        </h2>

                        <p>
                            ARXIA decision is currently within
                            automated operating parameters.
                        </p>

                    </div>

                </div>

            </section>


            <!-- =================================================
                 REVIEW SUMMARY
                 ================================================= -->

            <div class="review-summary">


                <section class="dashboard-card review-stat">

                    <span class="metric-label">
                        REVIEW PRIORITY
                    </span>

                    <div class="review-stat-value">
                        LOW
                    </div>

                </section>


                <section class="dashboard-card review-stat">

                    <span class="metric-label">
                        LAST REVIEW
                    </span>

                    <div class="review-stat-value">
                        01:21:42
                    </div>

                </section>


            </div>


            <!-- =================================================
                 REVIEW CONDITIONS
                 ================================================= -->

            <section class="dashboard-card review-conditions-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            REVIEW CONDITIONS
                        </span>

                    </div>

                </div>


                <div class="review-conditions">


                    <!-- AI SIGNAL -->

                    <div class="review-condition">

                        <span class="review-condition-name">
                            AI SIGNAL
                        </span>

                        <strong>
                            78%
                        </strong>

                        <span class="review-condition-status">

                            <span>✓</span>

                            CLEAR

                        </span>

                    </div>


                    <!-- RISK LEVEL -->

                    <div class="review-condition">

                        <span class="review-condition-name">
                            RISK LEVEL
                        </span>

                        <strong>
                            LOW
                        </strong>

                        <span class="review-condition-status">

                            <span>✓</span>

                            CLEAR

                        </span>

                    </div>


                    <!-- DECISION CONFIDENCE -->

                    <div class="review-condition">

                        <span class="review-condition-name">
                            DECISION CONFIDENCE
                        </span>

                        <strong>
                            82%
                        </strong>

                        <span class="review-condition-status">

                            <span>✓</span>

                            CLEAR

                        </span>

                    </div>


                    <!-- RACE CONDITIONS -->

                    <div class="review-condition">

                        <span class="review-condition-name">
                            RACE CONDITIONS
                        </span>

                        <strong>
                            STABLE
                        </strong>

                        <span class="review-condition-status">

                            <span>✓</span>

                            CLEAR

                        </span>

                    </div>


                </div>

            </section>


            <!-- =================================================
                 SYSTEM RECOMMENDATION
                 ================================================= -->

            <section class="dashboard-card review-recommendation-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            SYSTEM RECOMMENDATION
                        </span>

                    </div>


                    <div class="review-recommendation-status">

                        <span></span>

                        CLEAR

                    </div>

                </div>


                <div class="review-recommendation">

                    <p>
                        No human intervention is currently required.
                    </p>

                </div>

            </section>


        </div>

    `;
}


/* ============================================================
   SYSTEM METRICS MODULE
   ============================================================ */

function renderMetrics() {

    moduleContainer.innerHTML = `

        <div class="metrics-module">

            <div class="metrics-header">

                <div>

                    <span class="card-kicker">
                        SYSTEM METRICS
                    </span>

                    <h2>
                        How did the decision system perform?
                    </h2>

                </div>

                <div class="metrics-live">

                    <span></span>

                    LIVE

                </div>

            </div>


            <div class="metrics-summary">


                <section class="dashboard-card metrics-stat">

                    <span class="metric-label">
                        DECISIONS
                    </span>

                    <div class="metrics-stat-value">

                        <strong>
                            1,284
                        </strong>

                    </div>

                    <span class="metrics-stat-sub">
                        TOTAL PROCESSED
                    </span>

                </section>


                <section class="dashboard-card metrics-stat">

                    <span class="metric-label">
                        AI CONFIDENCE
                    </span>

                    <div class="metrics-stat-value">

                        <strong>
                            78%
                        </strong>

                    </div>

                    <span class="metrics-stat-sub">
                        CURRENT
                    </span>

                </section>


                <section class="dashboard-card metrics-stat">

                    <span class="metric-label">
                        RESPONSE TIME
                    </span>

                    <div class="metrics-stat-value">

                        <strong>
                            142
                        </strong>

                        <span>
                            ms
                        </span>

                    </div>

                    <span class="metrics-stat-sub">
                        AVG LATENCY
                    </span>

                </section>


                <section class="dashboard-card metrics-stat">

                    <span class="metric-label">
                        HUMAN OVERRIDE
                    </span>

                    <div class="metrics-stat-value">

                        <strong>
                            2.1%
                        </strong>

                    </div>

                    <span class="metrics-stat-sub">
                        RATE
                    </span>

                </section>


            </div>


            <section class="dashboard-card metrics-performance-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            SYSTEM PERFORMANCE
                        </span>

                    </div>

                </div>


                <div class="metrics-performance-list">


                    <div class="metrics-performance-row">

                        <div class="metrics-performance-label">

                            <span>
                                DECISION ACCURACY
                            </span>

                            <strong>
                                94%
                            </strong>

                        </div>

                        <div class="metrics-performance-bar">

                            <span style="width: 94%"></span>

                        </div>

                    </div>


                    <div class="metrics-performance-row">

                        <div class="metrics-performance-label">

                            <span>
                                SIGNAL CONSISTENCY
                            </span>

                            <strong>
                                96%
                            </strong>

                        </div>

                        <div class="metrics-performance-bar">

                            <span style="width: 96%"></span>

                        </div>

                    </div>


                    <div class="metrics-performance-row">

                        <div class="metrics-performance-label">

                            <span>
                                RISK DETECTION
                            </span>

                            <strong>
                                91%
                            </strong>

                        </div>

                        <div class="metrics-performance-bar">

                            <span style="width: 91%"></span>

                        </div>

                    </div>


                    <div class="metrics-performance-row">

                        <div class="metrics-performance-label">

                            <span>
                                RESPONSE EFFICIENCY
                            </span>

                            <strong>
                                98%
                            </strong>

                        </div>

                        <div class="metrics-performance-bar">

                            <span style="width: 98%"></span>

                        </div>

                    </div>


                </div>

            </section>


            <section class="dashboard-card metrics-status-card">

                <div class="card-header">

                    <div>

                        <span class="card-kicker">
                            SYSTEM STATUS
                        </span>

                    </div>

                </div>


                <div class="metrics-status-list">


                    <div class="metrics-status-item">

                        <span class="status-dot online"></span>

                        <span>
                            AI ENGINE
                        </span>

                        <strong>
                            ONLINE
                        </strong>

                    </div>


                    <div class="metrics-status-item">

                        <span class="status-dot online"></span>

                        <span>
                            TELEMETRY
                        </span>

                        <strong>
                            LIVE
                        </strong>

                    </div>


                    <div class="metrics-status-item">

                        <span class="status-dot online"></span>

                        <span>
                            DECISION CORE
                        </span>

                        <strong>
                            READY
                        </strong>

                    </div>


                </div>

            </section>

        </div>

    `;
}


/* ============================================================
   PLACEHOLDER MODULE
   ============================================================ */

function renderPlaceholder(module) {

    moduleContainer.innerHTML = `

        <div class="module-placeholder">

            <div class="placeholder-mark">
                ${module.icon}
            </div>

            <div class="placeholder-kicker">
                MODULE ${module.number}
            </div>

            <h2>
                ${module.title}
            </h2>

            <p>
                ${module.description}
            </p>

        </div>

    `;
}


/* ============================================================
   MODULE SELECTION
   ============================================================ */

function selectModule(moduleName) {

    const module =
        modules[moduleName];

    if (!module) {
        return;
    }


    /* --------------------------------------------------------
       Navigation state
       -------------------------------------------------------- */

    navItems.forEach((item) => {

        item.classList.toggle(
            "active",
            item.dataset.module === moduleName
        );

    });


    /* --------------------------------------------------------
       Page heading
       -------------------------------------------------------- */

    if (pageTitle) {

        pageTitle.textContent =
            module.title;

    }


    if (pageDescription) {

        pageDescription.textContent =
            module.description;

    }


    /* --------------------------------------------------------
       Eyebrow
       -------------------------------------------------------- */

    if (eyebrow) {

        eyebrow.textContent =
            `${module.number} / ${module.section}`;

    }


    /* --------------------------------------------------------
       Render selected module
       -------------------------------------------------------- */

    if (moduleName === "overview") {

    renderOverview();

    } else if (moduleName === "analysis") {

        renderAnalysis();

    } else if (moduleName === "timeline") {

        renderTimeline();

    } else if (moduleName === "comparison") {

        renderComparison();

    } else if (moduleName === "risk") {

        renderRisk();
    
    } else if (moduleName === "decision") {

        renderDecision();
    
    } else if (moduleName === "review") {

        renderReview();

    } else if (moduleName === "timeline") {

        renderTimeline();

    } else if (moduleName === "metrics") {

    renderMetrics();

} 
    
    else {

        renderPlaceholder(module);

    }


}


/* ============================================================
   NAVIGATION EVENTS
   ============================================================ */

navItems.forEach((item) => {

    item.addEventListener(
        "click",
        () => {

            selectModule(
                item.dataset.module
            );

        }
    );

});


/* ============================================================
   SYSTEM CLOCK
   ============================================================ */

function updateSystemTime() {

    if (!systemTime) {
        return;
    }


    const now =
        new Date();


    const hours =
        String(now.getHours())
            .padStart(2, "0");


    const minutes =
        String(now.getMinutes())
            .padStart(2, "0");


    const seconds =
        String(now.getSeconds())
            .padStart(2, "0");


    systemTime.textContent =
        `${hours}:${minutes}:${seconds}`;

}


updateSystemTime();


setInterval(
    updateSystemTime,
    1000
);


/* ============================================================
   INITIAL MODULE
   ============================================================ */

selectModule("overview");

setInterval(async () => {
    try {
        const response = await fetch("http://127.0.0.1:8000/analyze", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                circuit: "Monaco",
                session: "race",
                lap: 20,
                driver: "Test Driver",
                team: "Test Team",
                position: 4,
                event_type: "strategic_opportunity",
                description: "Actualización de estado en vivo"
            })
        });
        const result = await response.json();
        
        if (result.race_event) {
            raceState.lap = result.race_event.lap;
            raceState.position = result.race_event.position;
        }
        if (result.decision) {
            raceState.decision.action = result.decision.action;
            raceState.decision.confidence = Math.round((result.decision.confidence || 0) * 100);
            raceState.decision.description = result.decision.rationale;
        }
        if (result.risk_assessment) {
            raceState.raceSituation.title = `RIESGO: ${result.risk_assessment.risk_level.toUpperCase()}`;
            raceState.raceSituation.description = result.risk_assessment.explanation;
        }

        selectModule(document.querySelector('.nav-item.active').dataset.module);
    } catch (error) {
        console.error('Error al actualizar:', error);
    }
}, 3000);