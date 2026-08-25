/**
 * Converted from stitch_ascent_educator_dashboard/prerequisite_gap_map_high_contrast/prerequisite_gap_map_high_contrast.html
 */
export default function PrerequisiteGapMapHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-on-secondary -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-[#FFFFFF] tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-secondary-container font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="dashboard" href="#"><span className="material-symbols-outlined text-surface-variant/80">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="my-classes" href="#"><span className="material-symbols-outlined text-surface-variant/80">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="students" href="#"><span className="material-symbols-outlined text-surface-variant/80">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="attendance" href="#"><span className="material-symbols-outlined text-surface-variant/80">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="lesson-plans" href="#"><span className="material-symbols-outlined text-surface-variant/80">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="assignments" href="#"><span className="material-symbols-outlined text-surface-variant/80">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-[#FFFFFF] uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined text-surface-variant/80">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined text-surface-variant/80">route</span>Reasoning Paths</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 font-semibold border-l-4 border-secondary text-[#FFFFFF]" data-path="gap-map" href="#"><span className="material-symbols-outlined text-secondary-container">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined text-surface-variant/80">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="tracking" href="#"><span className="material-symbols-outlined text-surface-variant/80">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined text-surface-variant/80">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="content-verification" href="#"><span className="material-symbols-outlined text-surface-variant/80">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 transition-all gap-3 text-[#FFFFFF]" data-path="settings" href="#"><span className="material-symbols-outlined text-surface-variant/80">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-surface-variant">search</span><input className="bg-transparent border-none outline-none text-[#FFFFFF] w-full font-body-md" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-surface-variant hover:text-secondary-container transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-[#FFFFFF]">Dr. Sarah Ascent</div><div className="text-label-sm text-[#FFFFFF]">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-surface-variant"><div className="flex flex-col w-full">
<div className="flex flex-col gap-margin-desktop">
{/* Header Section */}
<div className="flex items-end justify-between flex-wrap gap-4">
<div className="flex flex-col gap-2">
<h1 className="font-display-lg text-display-lg text-[#FFFFFF]">Prerequisite Gap Map</h1>
<p className="font-body-lg text-body-lg max-w-2xl text-[#FFFFFF]">
          Visualizing foundational knowledge gaps for the current unit. Identify critical bottlenecks where intervention is needed before progressing.
        </p>
</div>
<div className="flex items-center gap-4">
<select className="bg-surface-container border-none outline-none font-title-md text-title-md text-[#1A1A1A] px-4 py-2 rounded-lg cursor-pointer hover:bg-surface-container-high transition-colors">
<option>Unit 4: Quadratic Equations</option>
<option>Unit 3: Linear Systems</option>
<option>Unit 2: Polynomials</option>
</select>
<button className="bg-secondary text-[#1A1A1A] px-6 py-2 rounded-lg font-title-md text-title-md hover:opacity-90 transition-opacity shadow-md">
          Export Map
        </button>
</div>
</div>
{/* Main Content Area */}
<div className="grid grid-cols-1 lg:grid-cols-4 gap-gutter">
{/* Gap Map Visualization */}
<div className="lg:col-span-3 bg-inverse-surface rounded-xl shadow-xl overflow-hidden relative min-h-[600px] flex flex-col">
{/* Visualization Controls */}
<div className="p-6 flex items-center justify-between z-10 bg-gradient-to-b from-inverse-surface/80 to-transparent">
<div className="flex items-center gap-3">
<span className="material-symbols-outlined text-surface-variant">my_location</span>
<span className="font-title-md text-title-md text-[#FFFFFF]">Current Focus: Quadratic Equations</span>
</div>
<div className="flex items-center gap-4 bg-surface-variant/10 px-4 py-2 rounded-full border border-surface-variant/20">
<span className="font-label-sm text-label-sm text-[#FFFFFF] uppercase tracking-widest">Gap Severity</span>
<div className="flex items-center gap-2">
<div className="w-3 h-3 rounded-full bg-surface-container-high"></div>
<span className="font-label-sm text-label-sm text-[#FFFFFF]">Low (0-15%)</span>
</div>
<div className="flex items-center gap-2">
<div className="w-3 h-3 rounded-full bg-secondary-container"></div>
<span className="font-label-sm text-label-sm text-[#FFFFFF]">Medium (16-35%)</span>
</div>
<div className="flex items-center gap-2">
<div className="w-3 h-3 rounded-full bg-error-container"></div>
<span className="font-label-sm text-label-sm text-[#FFFFFF]">Critical (&gt;35%)</span>
</div>
</div>
</div>
{/* The Node Map Canvas (Simulated with HTML/SVG) */}
<div className="flex-1 relative p-8 flex flex-col items-center justify-start overflow-auto">
{/* Connection Lines (SVG) */}
<svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: '0' }}>
<defs>
<linearGradient id="line-grad-1" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="#bfc9c4" stop-opacity="0.5"></stop>
<stop offset="100%" stop-color="#ffdad6" stop-opacity="0.8"></stop>
</linearGradient>
<linearGradient id="line-grad-2" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="#bfc9c4" stop-opacity="0.5"></stop>
<stop offset="100%" stop-color="#fed65b" stop-opacity="0.8"></stop>
</linearGradient>
<linearGradient id="line-grad-3" x1="0" x2="0" y1="0" y2="1">
<stop offset="0%" stop-color="#bfc9c4" stop-opacity="0.5"></stop>
<stop offset="100%" stop-color="#e8e8ea" stop-opacity="0.4"></stop>
</linearGradient>
</defs>
{/* Central Node to Level 1 */}
<path className="animate-[dash_20s_linear_infinite]" d="M 50% 120 Q 50% 180, 25% 240" fill="none" stroke="url(#line-grad-2)" stroke-dasharray="6,6" strokeWidth="3"></path>
<path d="M 50% 120 Q 50% 180, 50% 240" fill="none" stroke="url(#line-grad-1)" strokeWidth="4"></path>
<path d="M 50% 120 Q 50% 180, 75% 240" fill="none" stroke="url(#line-grad-3)" strokeWidth="2"></path>
{/* Level 1 to Level 2 */}
<path d="M 25% 320 Q 25% 380, 15% 440" fill="none" stroke="url(#line-grad-1)" strokeWidth="3"></path>
<path d="M 25% 320 Q 25% 380, 35% 440" fill="none" stroke="url(#line-grad-3)" strokeWidth="2"></path>
<path d="M 50% 320 Q 50% 380, 50% 440" fill="none" stroke="url(#line-grad-2)" strokeWidth="3"></path>
</svg>
{/* Nodes Layer */}
<div className="relative z-10 w-full flex flex-col items-center">
{/* Level 0: Current Topic */}
<div className="bg-primary-container px-8 py-4 rounded-xl shadow-lg border border-primary-fixed/20 hover:scale-105 transition-transform cursor-pointer relative group">
<div className="absolute -inset-2 bg-primary-fixed/10 rounded-2xl blur-lg group-hover:bg-primary-fixed/20 transition-colors"></div>
<h2 className="font-headline-lg text-headline-lg relative z-10 text-[#FFFFFF]">Quadratic Equations</h2>
<div className="font-label-sm text-label-sm text-center mt-1 relative z-10 text-[#FFFFFF]">Target Concept</div>
</div>
{/* Level 1: Immediate Prerequisites */}
<div className="w-full flex justify-around mt-24">
{/* Node 1.1 */}
<div className="bg-secondary-container p-5 rounded-xl shadow-md w-64 hover:-translate-y-1 transition-transform cursor-pointer relative group">
<div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 bg-inverse-surface font-label-sm text-label-sm px-2 py-1 rounded-full shadow-sm text-[#FFFFFF]">
                            22% Gap
                        </div>
<h3 className="font-title-md text-title-md mb-2 text-[#1A1A1A]">Factoring Trinomials</h3>
<div className="flex items-center gap-2">
<div className="flex-1 bg-on-secondary-container/10 h-2 rounded-full overflow-hidden">
<div className="bg-secondary w-[22%] h-full rounded-full"></div>
</div>
<span className="font-label-sm text-label-sm text-[#1A1A1A]">7/32</span>
</div>
</div>
{/* Node 1.2 (Critical) */}
<div className="bg-error-container p-5 rounded-xl shadow-md w-64 hover:-translate-y-1 transition-transform cursor-pointer ring-2 ring-error/30 relative group">
<div className="absolute -inset-1 bg-error-container blur-md opacity-50 group-hover:opacity-100 transition-opacity rounded-xl"></div>
<div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 bg-inverse-surface font-label-sm text-label-sm px-2 py-1 rounded-full shadow-sm z-20 text-[#FFFFFF]">
                            45% Gap
                        </div>
<h3 className="font-title-md text-title-md mb-2 relative z-10 text-[#1A1A1A]">Square Roots &amp; Radicals</h3>
<div className="flex items-center gap-2 relative z-10">
<div className="flex-1 bg-on-error-container/10 h-2 rounded-full overflow-hidden">
<div className="bg-error w-[45%] h-full rounded-full"></div>
</div>
<span className="font-label-sm text-label-sm font-bold text-[#1A1A1A]">14/32</span>
</div>
</div>
{/* Node 1.3 */}
<div className="bg-surface-container-high p-5 rounded-xl shadow-md w-64 hover:-translate-y-1 transition-transform cursor-pointer relative group">
<div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 bg-inverse-surface font-label-sm text-label-sm px-2 py-1 rounded-full shadow-sm text-[#FFFFFF]">
                            9% Gap
                        </div>
<h3 className="font-title-md text-title-md mb-2 text-[#1A1A1A]">Linear Equations</h3>
<div className="flex items-center gap-2">
<div className="flex-1 bg-on-surface/10 h-2 rounded-full overflow-hidden">
<div className="bg-on-surface-variant w-[9%] h-full rounded-full"></div>
</div>
<span className="font-label-sm text-label-sm text-[#1A1A1A]">3/32</span>
</div>
</div>
</div>
{/* Level 2: Deep Foundations */}
<div className="w-full flex justify-between px-32 mt-24">
{/* Node 2.1 (Under 1.1) */}
<div className="bg-error-container p-4 rounded-lg shadow-md w-48 hover:-translate-y-1 transition-transform cursor-pointer relative group">
<div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 bg-inverse-surface font-label-sm text-label-sm px-2 py-1 rounded-full shadow-sm text-[#FFFFFF]">
                            38% Gap
                        </div>
<h3 className="font-body-md text-body-md font-semibold mb-2 text-[#1A1A1A]">Distributive Property</h3>
</div>
{/* Node 2.2 (Under 1.1) */}
<div className="bg-surface-container-high p-4 rounded-lg shadow-md w-48 hover:-translate-y-1 transition-transform cursor-pointer relative group">
<div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 bg-inverse-surface font-label-sm text-label-sm px-2 py-1 rounded-full shadow-sm text-[#FFFFFF]">
                            12% Gap
                        </div>
<h3 className="font-body-md text-body-md font-semibold mb-2 text-[#1A1A1A]">Integer Operations</h3>
</div>
{/* Node 2.3 (Under 1.2) */}
<div className="bg-secondary-container p-4 rounded-lg shadow-md w-48 hover:-translate-y-1 transition-transform cursor-pointer relative group mr-[10%]">
<div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 bg-inverse-surface font-label-sm text-label-sm px-2 py-1 rounded-full shadow-sm text-[#FFFFFF]">
                            28% Gap
                        </div>
<h3 className="font-body-md text-body-md font-semibold mb-2 text-[#1A1A1A]">Perfect Squares</h3>
</div>
</div>
</div>
</div>
</div>
{/* Detail Panel */}
<div className="flex flex-col gap-6">
{/* Node Details */}
<div className="bg-surface rounded-xl p-card-padding shadow-md flex flex-col gap-4 h-fit">
<div className="flex items-start justify-between border-b border-surface-variant/20 pb-4">
<div>
<div className="font-label-sm text-label-sm uppercase tracking-widest mb-1 text-[#1A1A1A]">Selected Node</div>
<h3 className="font-headline-lg text-headline-lg text-[#1A1A1A]">Square Roots &amp; Radicals</h3>
</div>
<div className="bg-error-container w-12 h-12 rounded-full flex items-center justify-center font-title-md text-title-md text-[#1A1A1A]">
                    45%
                </div>
</div>
<div className="flex flex-col gap-2">
<span className="font-title-md text-title-md text-[#1A1A1A]">At Risk Students (14)</span>
<p className="font-body-md text-body-md text-[#1A1A1A]">
                    These students demonstrate fundamental misunderstandings in simplifying radicals, which will block progress in the quadratic formula.
                </p>
</div>
<div className="flex flex-col gap-2 mt-2">
<div className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg hover:bg-surface-container transition-colors cursor-pointer">
<div className="flex items-center gap-3">
<div className="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center font-label-sm text-label-sm text-[#1A1A1A]">JS</div>
<span className="font-body-md text-body-md font-semibold text-[#1A1A1A]">James Smith</span>
</div>
<span className="material-symbols-outlined text-surface-variant">chevron_right</span>
</div>
<div className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg hover:bg-surface-container transition-colors cursor-pointer">
<div className="flex items-center gap-3">
<div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center font-label-sm text-label-sm text-[#FFFFFF]">EW</div>
<span className="font-body-md text-body-md font-semibold text-[#1A1A1A]">Emma Wright</span>
</div>
<span className="material-symbols-outlined text-surface-variant">chevron_right</span>
</div>
<button className="font-title-md text-title-md mt-2 text-left hover:underline text-[#1A1A1A]">View all 14 students</button>
</div>
</div>
{/* AI Recommendation */}
<div className="bg-primary-container rounded-xl p-card-padding shadow-md flex flex-col gap-4 relative overflow-hidden">
<div className="absolute -right-12 -top-12 w-32 h-32 bg-primary-fixed/20 rounded-full blur-2xl pointer-events-none"></div>
<div className="flex items-center gap-2">
<span className="material-symbols-outlined font-variation-settings-'FILL' 1 text-secondary-container">psychology</span>
<span className="font-label-sm text-label-sm uppercase tracking-widest text-[#FFFFFF]">AI Action Plan</span>
</div>
<h4 className="font-title-md text-title-md text-[#FFFFFF]">Suggested Intervention</h4>
<p className="font-body-md text-body-md text-[#FFFFFF]">
                 Before introducing the Quadratic Formula on Thursday, run a 15-minute targeted small-group session on simplifying non-perfect square radicals for the 14 at-risk students.
             </p>
<button className="bg-primary-fixed text-[#1A1A1A] px-4 py-2 rounded-lg font-title-md text-title-md mt-2 hover:bg-primary-fixed-dim transition-colors flex justify-center items-center gap-2">
                 Generate Mini-Lesson
                 <span className="material-symbols-outlined text-[18px]">auto_fix_high</span>
</button>
</div>
</div>
</div>
</div>
</div>
</main></div>

    </>
  );
}
