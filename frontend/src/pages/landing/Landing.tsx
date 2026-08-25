import React, { useEffect } from "react";
import "./Landing.css";

const Landing: React.FC = () => {
  useEffect(() => {
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    const slides = document.querySelectorAll<HTMLElement>(".slide");

    if (reduced || !("IntersectionObserver" in window)) {
      slides.forEach((slide) => {
        slide.classList.add("is-visible");
      });

      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.2,
      }
    );

    slides.forEach((slide) => observer.observe(slide));

    return () => observer.disconnect();
  }, []);

  return (
    <main className="scroll-story">

      {/* =========================================================
          REUSABLE SCAFFOLD SVG
      ========================================================= */}

      <svg
        width="0"
        height="0"
        style={{ position: "absolute" }}
        aria-hidden="true"
      >
        <symbol id="rig" viewBox="0 0 200 260">
          <g
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
          >
            <path d="M28 12v240M96 12v240M164 12v240" />
            <path d="M14 64h172M14 132h172M14 200h172" />
            <path d="M28 64 96 12M96 132l68-52M28 200l68-54" />
            <path d="M18 252h20M86 252h20M154 252h20" />

            <g strokeWidth="2">
              <path d="M112 140v56M136 140v56" />
              <path d="M112 152h24M112 166h24M112 180h24" />
            </g>
          </g>
        </symbol>
      </svg>

      {/* =========================================================
          SLIDE 1 — FRONT PAGE
      ========================================================= */}

      <section className="slide slide-news">
        <div className="scaffold tilt" />

        <div className="rig a" aria-hidden="true">
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <div className="rig b" aria-hidden="true">
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <h2 className="sr-only">
          A mock front page asking what happens to student thinking as AI use
          rises
        </h2>

        <div className="sheet-wrap reveal">
          <span className="tape tl" />
          <span className="tape tr" />

          <div className="paper-sheet">
            <h1 className="masthead">
              <span className="the">
                The classroom paper · first look
              </span>
              The Daily Edge
            </h1>

            <div className="masthead-meta">
              <span>Vol. 1 — No. 04</span>
              <span>Homework &amp; Learning</span>
              <span>This week</span>
            </div>

            <div className="news-grid">
              <div>
                <span className="kicker">
                  Reported from ordinary classrooms
                </span>

                <h2 className="headline">
                  Students are using AI more.
                  <br />
                  Are they <em>thinking</em> less?
                </h2>

                <p className="subhead">
                  A quiet look at what happens when help becomes the whole
                  homework.
                </p>

                <div className="article-body">
                  <p>
                    Teachers this term describe a familiar stack of
                    assignments: fluent, tidy, and oddly distant from what was
                    taught in the room.
                  </p>

                  <p>
                    Usage is rising. The open question is a smaller one —
                    whether reaching for an answer is beginning to stand in
                    for reasoning toward it.
                  </p>
                </div>
              </div>

              <aside className="news-side">
                <div className="sticky s-orange">
                  <b>Noticed</b>
                  Same closing sentence, four different subjects.
                </div>

                <div className="sticky s-sky">
                  <b>Asked</b>
                  “Can you explain your second step?” — often, silence.
                </div>

                <div className="sticky s-lime">
                  <b>Not settled</b>
                  None of this is proof. It is worth looking at.
                </div>
              </aside>
            </div>
          </div>
        </div>

        <div
          className="scroll-cue reveal"
          style={{ "--rd": ".4s" } as React.CSSProperties}
        >
          Scroll ↓
        </div>
      </section>

      {/* =========================================================
          SLIDE 2 — A DESK OF PAGES
      ========================================================= */}

      <section className="slide slide-papers">
        <div className="scaffold" />

        <div className="rig c" aria-hidden="true">
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <h2 className="sr-only">
          Assignments from several subjects, all reading with a similar
          borrowed rhythm
        </h2>

        <div className="stack">
          <span className="eyebrow">
            One week, one class
          </span>

          <h2 className="title-lg">
            A similar voice, <em>across subjects.</em>
          </h2>

          <p
            className="body-md"
            style={{ maxWidth: "40ch" }}
          >
            Different pages, a rhythm that starts to repeat.
          </p>

          <div className="board">
            <div
              className="p-card p1 reveal"
              style={{ "--rd": ".06s" } as React.CSSProperties}
            >
              <div className="who">History</div>
              Rigid alliances left little room for a diplomatic resolution
              before war broke out.
            </div>

            <div
              className="p-card p2 reveal"
              style={{ "--rd": ".14s" } as React.CSSProperties}
            >
              <div className="who">Biology</div>
              Enzymes lower the activation energy a reaction needs, so
              metabolism can proceed.
            </div>

            <div
              className="p-card p3 reveal"
              style={{ "--rd": ".22s" } as React.CSSProperties}
            >
              <div className="who">Economics</div>
              When supply tightens and demand holds, price settles at a new
              equilibrium.
            </div>

            <div
              className="p-card p4 reveal"
              style={{ "--rd": ".3s" } as React.CSSProperties}
            >
              <div className="who">Physics</div>
              Every action produces an equal and opposite reaction, at every
              scale.
            </div>

            <div
              className="p-card p5 reveal"
              style={{ "--rd": ".38s" } as React.CSSProperties}
            >
              <div className="who">Literature</div>
              An unreliable narrator asks the reader to question each claim.
            </div>

            <span
              className="p-count reveal"
              style={{ "--rd": ".46s" } as React.CSSProperties}
            >
              37 assignments · one week
            </span>
          </div>
        </div>
      </section>

      {/* =========================================================
          SLIDE 3 — THE SAME CLOSING LINE
      ========================================================= */}

      <section className="slide slide-similar">
        <div className="scaffold tilt" />

        <h2 className="sr-only">
          Three assignments from three students closing on the same templated
          sentence
        </h2>

        <div className="stack">
          <span className="eyebrow">
            Look closer
          </span>

          <h2 className="title-lg">
            Different homework.
            <br />
            The same <em>fingerprint.</em>
          </h2>

          <p
            className="body-md"
            style={{ maxWidth: "34ch" }}
          >
            The words change. The pattern holds.
          </p>

          <div className="fan">
            <div
              className="a-card a1 reveal"
              style={{ "--rd": ".08s" } as React.CSSProperties}
            >
              <div className="who">R. Alvarez</div>
              Photosynthesis stores sunlight as chemical energy.{" "}
              <mark>In conclusion, it is important to note that</mark>{" "}
              this process sustains nearly all life on Earth.
            </div>

            <div
              className="a-card a2 reveal"
              style={{ "--rd": ".18s" } as React.CSSProperties}
            >
              <div className="who">M. Chen</div>
              The First World War grew from a web of alliances.{" "}
              <mark>In conclusion, it is important to note that</mark>{" "}
              these tensions made wide conflict hard to avoid.
            </div>

            <div
              className="a-card a3 reveal"
              style={{ "--rd": ".28s" } as React.CSSProperties}
            >
              <div className="who">P. Fernandes</div>
              Supply and demand set market price together.{" "}
              <mark>In conclusion, it is important to note that</mark>{" "}
              equilibrium balances both sides of a market.
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          SLIDE 4 — SCAFFOLD
      ========================================================= */}

      <section className="slide slide-shift">
        <div className="scaffold" />

        <div
          className="rig a"
          aria-hidden="true"
          style={{ opacity: 0.13 }}
        >
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <div
          className="rig b"
          aria-hidden="true"
          style={{ opacity: 0.13 }}
        >
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <h2 className="sr-only">
          Scaffold — support that stays close to the curriculum, and comes
          away when it isn't needed
        </h2>

        <div className="brand-plate reveal">
          <span className="name">
            Scaffold
          </span>

          <span className="kind">
            learning support, not a shortcut
          </span>
        </div>

        <p
          className="shout reveal"
          style={{ "--rd": ".12s" } as React.CSSProperties}
        >
          <span className="l1">
            Not another shortcut.
          </span>

          <span className="l2">
            A staircase.
          </span>
        </p>

        <p
          className="shift-sub reveal"
          style={{ "--rd": ".22s" } as React.CSSProperties}
        >
          Scaffolding holds the work while it is being built — and comes away
          once the student can stand on it.
        </p>

        <div
          className="cta-row reveal"
          style={{ "--rd": ".32s" } as React.CSSProperties}
        >
          <a
            href="#how"
            className="btn"
          >
            Start with your syllabus

            <svg
              viewBox="0 0 24 24"
              width="15"
              height="15"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14" />
              <path d="M13 6l6 6-6 6" />
            </svg>
          </a>

          <a
            href="#how"
            className="btn ghost"
          >
            See how it works
          </a>
        </div>
      </section>

      {/* =========================================================
          SLIDE 5 — GROUNDED
      ========================================================= */}

      <section
        className="slide slide-curriculum"
        id="how"
      >
        <div className="scaffold" />

        <div className="rig c" aria-hidden="true">
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <div className="stack">
          <span className="eyebrow">
            Grounded
          </span>

          <h2 className="title-lg reveal">
            Answers trace back to a page in your{" "}
            <em>own</em> course material.
          </h2>

          <div
            className="lesson-card reveal"
            style={{ "--rd": ".16s" } as React.CSSProperties}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "1em",
              }}
            >
              <span className="tag">
                Grade 8 · Algebra
              </span>

              <span className="chip">
                Ch. 6 · p. 88
              </span>
            </div>

            <div
              className="title-md"
              style={{ marginTop: "1em" }}
            >
              Solving systems of equations
            </div>

            <p
              className="body-md"
              style={{ marginTop: ".4em" }}
            >
              Explained the way the syllabus explains it, with the page it
              came from.
            </p>

            <div style={{ marginTop: "1.4em" }}>
              <div
                className="note"
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: ".5em",
                }}
              >
                <span>Curriculum alignment</span>
                <span>88%</span>
              </div>

              <div className="bar">
                <span style={{ width: "88%" }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          SLIDE 6 — ONE FLOW
      ========================================================= */}

      <section className="slide slide-adaptive">
        <div className="scaffold tilt" />

        <div className="stack">
          <span className="eyebrow">
            How it moves
          </span>

          <h2
            className="title-lg reveal"
          >
            One flow, <em>continuous</em> system.
          </h2>

          <p
            className="body-md reveal"
            style={
              {
                "--rd": ".08s",
                maxWidth: "42ch",
              } as React.CSSProperties
            }
          >
            What happens between a question and understanding it.
          </p>

          <div className="flow">
            <div
              className="flow-step reveal"
              style={{ "--rd": ".16s" } as React.CSSProperties}
            >
              <span className="n">01</span>

              <div className="title-md">
                Finds the gap
              </div>

              <p>
                Where the reasoning actually slipped.
              </p>
            </div>

            <div
              className="flow-step reveal"
              style={{ "--rd": ".24s" } as React.CSSProperties}
            >
              <span className="n">02</span>

              <div className="title-md">
                Explains it again
              </div>

              <p>
                In the words the course already uses.
              </p>
            </div>

            <div
              className="flow-step reveal"
              style={{ "--rd": ".32s" } as React.CSSProperties}
            >
              <span className="n">03</span>

              <div className="title-md">
                Practises until it holds
              </div>

              <p>
                Short sets aimed at that one gap.
              </p>
            </div>
          </div>

          <div className="pair">
            <div
              className="reveal"
              style={{ "--rd": ".4s" } as React.CSSProperties}
            >
              <b>
                Cites its source
              </b>

              <span>
                Chapter and page, each time.
              </span>
            </div>

            <div
              className="reveal"
              style={{ "--rd": ".48s" } as React.CSSProperties}
            >
              <b>
                Says when it doesn't know
              </b>

              <span>
                No answer rather than an invention.
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          SLIDE 7 — EVIDENCE
      ========================================================= */}

      <section className="slide slide-evidence">
        <div className="scaffold" />

        <div className="rig b" aria-hidden="true">
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <div className="stack">
          <span className="eyebrow">
            Evidence first
          </span>

          <h2
            className="title-lg reveal"
          >
            When it isn't sure,
            <br />
            <em>it says so.</em>
          </h2>

          <div
            className="ev-quote reveal"
            style={{ "--rd": ".18s" } as React.CSSProperties}
          >
            <span className="q-tag">
              From a session
            </span>

            <p className="q-line">
              A student asks something the curriculum hasn't covered yet.
            </p>

            <p className="q-line">
              <b>Scaffold:</b>{" "}
              “The course material doesn't give me enough to answer this.
              Rather than filling the gap from elsewhere, I'll stop here.”
            </p>

            <p className="q-line">
              It goes to the teacher, to review before anything is shown.
            </p>
          </div>

          <div className="ev-steps">
            <div
              className="ev-step reveal"
              style={{ "--rd": ".28s" } as React.CSSProperties}
            >
              <em>01 · Check</em>
              Is there evidence in the approved material?
            </div>

            <div
              className="ev-step reveal"
              style={{ "--rd": ".34s" } as React.CSSProperties}
            >
              <em>02 · Stop</em>
              If not, no guess and no outside source.
            </div>

            <div
              className="ev-step reveal"
              style={{ "--rd": ".4s" } as React.CSSProperties}
            >
              <em>03 · Route</em>
              Held for the teacher to answer.
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          SLIDE 8 — TEACHER'S VIEW
      ========================================================= */}

      <section className="slide slide-teacher">
        <div className="scaffold tilt" />

        <h2 className="sr-only">
          The teacher's view: patterns across the class, drafted for review
        </h2>

        <div
          style={{
            position: "relative",
            zIndex: 2,
            textAlign: "center",
            marginBottom: "1.6em",
          }}
        >
          <span className="eyebrow reveal">
            The teacher's view
          </span>
        </div>

        <div
          className="dash reveal"
          style={{ "--rd": ".1s" } as React.CSSProperties}
        >
          <div className="dash-head">
            <span className="tag">
              Class insight
            </span>

            <span className="note">
              Drafted for you to edit
            </span>
          </div>

          <div className="dash-grid">
            <div
              className="dash-tile"
              style={
                {
                  "--accent": "var(--orange)",
                } as React.CSSProperties
              }
            >
              <div className="k">
                Shared misconception
              </div>

              <div className="v">
                Sign-error pattern
              </div>

              <div className="d">
                12 of 28 students · Ch. 5 reteach suggested
              </div>

              <div className="bar">
                <span style={{ width: "43%" }} />
              </div>
            </div>

            <div
              className="dash-tile"
              style={
                {
                  "--accent": "var(--sky)",
                } as React.CSSProperties
              }
            >
              <div className="k">
                Prerequisite gap
              </div>

              <div className="v">
                Factoring
              </div>

              <div className="d">
                8 students flagged before this unit begins
              </div>

              <div className="bar">
                <span style={{ width: "29%" }} />
              </div>
            </div>

            <div
              className="dash-tile"
              style={
                {
                  "--accent": "var(--lime)",
                } as React.CSSProperties
              }
            >
              <div className="k">
                Reasoning trace
              </div>

              <div className="v">
                Where the logic broke
              </div>

              <div className="d">
                The steps behind a wrong answer, not only the score
              </div>

              <span className="flagpill">
                Auto-logged
              </span>
            </div>

            <div
              className="dash-tile"
              style={
                {
                  "--accent": "var(--peach)",
                } as React.CSSProperties
              }
            >
              <div className="k">
                Held for review
              </div>

              <div className="v">
                Five open questions
              </div>

              <div className="d">
                No curriculum backing this week — waiting on you
              </div>

              <span
                className="flagpill"
                style={{
                  background: "var(--ink)",
                  color: "var(--paper)",
                }}
              >
                Needs you
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          SLIDE 9 — WHOLE CLASSROOM
      ========================================================= */}

      <section className="slide slide-final">
        <div className="scaffold" />

        <div className="rig a" aria-hidden="true">
          <svg>
            <use href="#rig" />
          </svg>
        </div>

        <span className="tag reveal">
          One curriculum.
        </span>

        <h2
          className="title-lg reveal"
          style={
            {
              "--rd": ".1s",
              marginTop: ".7em",
            } as React.CSSProperties
          }
        >
          Built for the <em>whole</em> classroom.
        </h2>

        <div className="eco">
          <div
            className="c1 reveal"
            style={{ "--rd": ".18s" } as React.CSSProperties}
          >
            Student
          </div>

          <div
            className="c2 reveal"
            style={{ "--rd": ".26s" } as React.CSSProperties}
          >
            Teacher
          </div>

          <div
            className="c3 reveal"
            style={{ "--rd": ".34s" } as React.CSSProperties}
          >
            School
          </div>
        </div>

        <div
          className="cta-row reveal"
          style={{ "--rd": ".44s" } as React.CSSProperties}
        >
          <a
            href="#login"
            className="btn"
          >
            Sign in

            <svg
              viewBox="0 0 24 24"
              width="15"
              height="15"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14" />
              <path d="M13 6l6 6-6 6" />
            </svg>
          </a>
        </div>
      </section>
    </main>
  );
};

export default Landing;