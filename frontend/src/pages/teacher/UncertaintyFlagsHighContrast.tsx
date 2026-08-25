/**
 * Converted from stitch_ascent_educator_dashboard/uncertainty_flags_high_contrast/uncertainty_flags_high_contrast.html
 */
export default function UncertaintyFlagsHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-white -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="dashboard" href="#"><span className="material-symbols-outlined">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="my-classes" href="#"><span className="material-symbols-outlined">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="students" href="#"><span className="material-symbols-outlined">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="attendance" href="#"><span className="material-symbols-outlined">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="lesson-plans" href="#"><span className="material-symbols-outlined">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="assignments" href="#"><span className="material-symbols-outlined">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="gap-map" href="#"><span className="material-symbols-outlined">map</span>Gap Map</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="tracking" href="#"><span className="material-symbols-outlined">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="content-verification" href="#"><span className="material-symbols-outlined">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-white">search</span><input className="bg-transparent border-none outline-none text-white placeholder-white w-full font-body-md" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-white hover:text-white transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-white">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full relative">
<div className="mb-margin-desktop relative">
<div className="absolute -top-10 -left-10 w-64 h-64 bg-secondary-fixed/20 rounded-full blur-3xl -z-10 mix-blend-multiply"></div>
<div className="absolute top-20 right-20 w-48 h-48 bg-primary/5 rounded-full blur-2xl -z-10"></div>
<div className="flex items-end justify-between w-full mb-6 relative z-10">
<div className="flex flex-col gap-2 max-w-2xl">
<div className="flex items-center gap-3 text-secondary">
<span className="material-symbols-outlined text-headline-lg font-headline-lg" style={{ fontVariationSettings: '\'FILL\' 1' }}>warning</span>
<span className="font-label-sm text-label-sm uppercase tracking-[0.1em] text-white">AI Insight Insight</span>
</div>
<h1 className="font-display-lg text-display-lg text-white">Uncertainty Flags</h1>
<p className="font-body-lg text-body-lg text-white mt-2 max-w-3xl">The AI has flagged the following responses as having insufficient evidence to determine a clear reasoning path or misconception. These require educator review to accurately assess student understanding.</p>
</div>
<div className="hidden lg:flex items-center gap-4">
<div className="bg-surface-container-high rounded-full px-6 py-3 flex items-center gap-3 shadow-sm border border-surface-variant/20">
<span className="font-label-sm text-label-sm text-black uppercase tracking-wider">Pending Review</span>
<span className="font-headline-lg text-headline-lg text-black">12</span>
</div>
</div>
</div>
</div>
<div className="flex items-center justify-between mb-8 border-b border-surface-variant/20 pb-4">
<div className="flex gap-4">
<button className="font-label-sm text-label-sm px-4 py-2 rounded-full bg-secondary text-white transition-all shadow-md">Needs Review (12)</button>
<button className="font-label-sm text-label-sm px-4 py-2 rounded-full text-white hover:bg-surface-container transition-all">Resolved (48)</button>
</div>
<div className="flex gap-2 text-white">
<button className="p-2 hover:bg-surface-container rounded-full transition-all flex items-center justify-center"><span className="material-symbols-outlined">filter_list</span></button>
<button className="p-2 hover:bg-surface-container rounded-full transition-all flex items-center justify-center"><span className="material-symbols-outlined">sort</span></button>
</div>
</div>
<div className="grid grid-cols-1 gap-6 relative z-10">
{/* Queue Item 1 */}
<div className="bg-surface-container-lowest rounded-xl p-card-padding shadow-[0_4px_20px_rgba(0,0,0,0.03)] border-2 border-dashed border-secondary/40 hover:border-secondary/80 hover:-translate-y-1 transition-all duration-300 relative group overflow-hidden">
{/* Decorative subtle glow on hover */}
<div className="absolute inset-0 bg-gradient-to-br from-secondary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
<div className="flex flex-col lg:flex-row gap-6 relative z-10">
{/* Meta Info */}
<div className="lg:w-1/4 flex flex-col gap-4 border-r border-surface-variant/20 pr-6">
<div className="flex items-center gap-3">
<div className="w-10 h-10 rounded-full bg-tertiary-fixed flex items-center justify-center text-black font-title-md text-title-md">
                            JD
                         </div>
<div>
<div className="font-title-md text-title-md text-black">Julian Davis</div>
<div className="font-label-sm text-label-sm text-black uppercase tracking-widest mt-1">Grade 10 Physics</div>
</div>
</div>
<div className="flex flex-col gap-1 mt-2">
<span className="font-label-sm text-label-sm uppercase text-black" style={{ opacity: '0' }}>Assignment</span>
<span className="font-body-md text-body-md text-black">Kinematics Quiz 2</span>
<span className="font-label-sm text-label-sm uppercase mt-2 text-black" style={{ opacity: '0' }}>Assignment</span>
<span className="font-body-md text-body-md text-black">10:42 AM, Today</span>
</div>
</div>
{/* Content & Issue */}
<div className="lg:w-1/2 flex flex-col gap-4">
<div>
<span className="font-label-sm text-label-sm uppercase mb-2 block text-black" style={{ opacity: '0' }}>Assignment</span>
<p className="font-body-lg text-body-lg text-black bg-surface-container p-4 rounded-lg italic">
                           "If a car accelerates from rest at 5 m/s² for 4 seconds, what is its final velocity?"
                        </p>
</div>
<div>
<span className="font-label-sm text-label-sm uppercase mb-2 block text-black" style={{ opacity: '0' }}>Assignment</span>
<p className="font-body-md text-body-md text-black bg-surface-container-high p-4 rounded-lg font-mono">
                           "The car goes 20 meters because 5 times 4 is 20. So the final velocity is 20m."
                        </p>
</div>
<div className="bg-error-container/30 border-l-4 border-error p-3 flex items-start gap-3 mt-2 rounded-r-lg">
<span className="material-symbols-outlined text-error mt-0.5">help_center</span>
<div>
<div className="font-title-md text-title-md text-black text-sm">AI Analysis Inconclusive</div>
<div className="font-body-md text-body-md mt-1 text-sm text-black">
                                The student calculated the correct numerical value (20) but applied incorrect units (meters instead of m/s) and reasoning ("goes 20 meters"). AI found insufficient evidence to determine if this is a calculation error, a unit confusion, or a fundamental misunderstanding of velocity vs. displacement.
                            </div>
</div>
</div>
</div>
{/* Action */}
<div className="lg:w-1/4 flex flex-col justify-between pl-4">
<div className="flex flex-col gap-2">
<span className="font-label-sm text-label-sm uppercase text-black" style={{ opacity: '0' }}>Assignment</span>
<button className="flex items-center gap-2 font-body-md text-body-md text-black hover:text-secondary transition-colors p-2 rounded-md hover:bg-surface-container-low text-left">
<span className="material-symbols-outlined text-lg">chat</span> Request Clarification
                         </button>
<button className="flex items-center gap-2 font-body-md text-body-md text-black hover:text-secondary transition-colors p-2 rounded-md hover:bg-surface-container-low text-left">
<span className="material-symbols-outlined text-lg">edit</span> Manually Grade
                         </button>
</div>
<button className="mt-6 w-full bg-secondary text-white font-title-md text-title-md py-3 px-6 rounded-lg shadow-md hover:shadow-lg hover:bg-secondary-fixed-dim hover:text-on-secondary-fixed-variant transition-all flex items-center justify-center gap-2 group/btn">
                         Review Interaction
                         <span className="material-symbols-outlined group-hover/btn:translate-x-1 transition-transform">arrow_forward</span>
</button>
</div>
</div>
</div>
{/* Queue Item 2 */}
<div className="bg-surface-container-lowest rounded-xl p-card-padding shadow-[0_4px_20px_rgba(0,0,0,0.03)] border-2 border-dashed border-secondary/40 hover:border-secondary/80 hover:-translate-y-1 transition-all duration-300 relative group overflow-hidden">
<div className="absolute inset-0 bg-gradient-to-br from-secondary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
<div className="flex flex-col lg:flex-row gap-6 relative z-10">
<div className="lg:w-1/4 flex flex-col gap-4 border-r border-surface-variant/20 pr-6">
<div className="flex items-center gap-3">
<div className="w-10 h-10 rounded-full bg-primary-fixed flex items-center justify-center text-black font-title-md text-title-md">
                            MP
                         </div>
<div>
<div className="font-title-md text-title-md text-black">Maya Patel</div>
<div className="font-label-sm text-label-sm text-black uppercase tracking-widest mt-1">AP World History</div>
</div>
</div>
<div className="flex flex-col gap-1 mt-2">
<span className="font-label-sm text-label-sm uppercase text-black" style={{ opacity: '0' }}>Assignment</span>
<span className="font-body-md text-body-md text-black">Industrial Revolution DBQ</span>
<span className="font-label-sm text-label-sm uppercase mt-2 text-black" style={{ opacity: '0' }}>Assignment</span>
<span className="font-body-md text-body-md text-black">Yesterday, 4:15 PM</span>
</div>
</div>
<div className="lg:w-1/2 flex flex-col gap-4">
<div>
<span className="font-label-sm text-label-sm uppercase mb-2 block text-black" style={{ opacity: '0' }}>Assignment</span>
<p className="font-body-lg text-body-lg text-black bg-surface-container p-4 rounded-lg italic line-clamp-2">
                           "Analyze the social consequences of urbanization during the early Industrial Revolution in Great Britain, citing specific evidence from Documents A and C."
                        </p>
</div>
<div>
<span className="font-label-sm text-label-sm uppercase mb-2 block text-black" style={{ opacity: '0' }}>Assignment</span>
<p className="font-body-md text-body-md text-black bg-surface-container-high p-4 rounded-lg font-mono">
                           "People moved to cities and it was bad. Document A says cities were crowded. Document C is about factories. They were tired."
                        </p>
</div>
<div className="bg-error-container/30 border-l-4 border-error p-3 flex items-start gap-3 mt-2 rounded-r-lg">
<span className="material-symbols-outlined text-error mt-0.5">help_center</span>
<div>
<div className="font-title-md text-title-md text-black text-sm">AI Analysis Inconclusive</div>
<div className="font-body-md text-body-md mt-1 text-sm text-black">
                                Response lacks sufficient detail or structural coherence for reliable automated rubric scoring. AI cannot determine if the student failed to understand the documents, rushed the response, or struggled with synthesis.
                            </div>
</div>
</div>
</div>
<div className="lg:w-1/4 flex flex-col justify-between pl-4">
<div className="flex flex-col gap-2">
<span className="font-label-sm text-label-sm uppercase text-black" style={{ opacity: '0' }}>Assignment</span>
<button className="flex items-center gap-2 font-body-md text-body-md text-black hover:text-secondary transition-colors p-2 rounded-md hover:bg-surface-container-low text-left">
<span className="material-symbols-outlined text-lg">history_edu</span> View Full Essay
                         </button>
<button className="flex items-center gap-2 font-body-md text-body-md text-black hover:text-secondary transition-colors p-2 rounded-md hover:bg-surface-container-low text-left">
<span className="material-symbols-outlined text-lg">schedule_send</span> Schedule Conference
                         </button>
</div>
<button className="mt-6 w-full bg-secondary text-white font-title-md text-title-md py-3 px-6 rounded-lg shadow-md hover:shadow-lg hover:bg-secondary-fixed-dim hover:text-on-secondary-fixed-variant transition-all flex items-center justify-center gap-2 group/btn">
                         Review Interaction
                         <span className="material-symbols-outlined group-hover/btn:translate-x-1 transition-transform">arrow_forward</span>
</button>
</div>
</div>
</div>
</div>
</div></main></div>

    </>
  );
}
