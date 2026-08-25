/**
 * Converted from stitch_ascent_educator_dashboard/suggested_reteach_high_contrast/suggested_reteach_high_contrast.html
 */
export default function SuggestedReteachHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-white -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="dashboard" href="#"><span className="material-symbols-outlined">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="my-classes" href="#"><span className="material-symbols-outlined">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="students" href="#"><span className="material-symbols-outlined">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="attendance" href="#"><span className="material-symbols-outlined">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="lesson-plans" href="#"><span className="material-symbols-outlined">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="assignments" href="#"><span className="material-symbols-outlined">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="gap-map" href="#"><span className="material-symbols-outlined">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="tracking" href="#"><span className="material-symbols-outlined">analytics</span>Tracking</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="content-verification" href="#"><span className="material-symbols-outlined">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-white">search</span><input className="bg-transparent border-none outline-none text-white w-full font-body-md" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-white hover:text-white transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-white">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full relative">
{/* Header / Intro */}
<div className="mb-10 lg:mb-16 max-w-3xl relative z-10">
<div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container rounded-full text-label-sm font-label-sm text-black tracking-widest uppercase mb-4 shadow-sm">
<span className="material-symbols-outlined text-secondary text-[16px]">psychology</span>
      Suggested Reteach Paths
    </div>
<h1 className="font-display-lg text-display-lg text-white mb-4">Precision Interventions</h1>
<p className="font-body-lg text-body-lg text-white max-w-2xl">
      Review and approve AI-generated mini-lessons targeted at specific misconceptions detected across your classes.
    </p>
</div>
{/* Decorative blur element */}
<div className="absolute top-0 right-10 w-96 h-96 bg-primary/5 rounded-full blur-[100px] pointer-events-none -z-10"></div>
{/* Main Feed Area */}
<div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10">
{/* Feed Column */}
<div className="lg:col-span-8 flex flex-col gap-6">
{/* Card 1 (High Priority / Gold Highlight) */}
<div className="relative bg-surface-container-lowest rounded-xl p-card-padding shadow-[0_4px_40px_rgba(0,0,0,0.03)] overflow-hidden flex flex-col group transition-transform duration-300 hover:-translate-y-1">
{/* Gold Accent Line */}
<div className="absolute left-0 top-0 bottom-0 w-1 bg-secondary shadow-[0_0_8px_rgba(212,175,55,0.4)]"></div>
<div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4 ml-3">
<div>
<div className="flex items-center gap-2 mb-1">
<span className="bg-error-container text-black px-2 py-0.5 rounded text-[11px] font-label-sm tracking-widest uppercase">High Priority</span>
<span className="text-label-sm font-label-sm text-black">Affects 14 Students</span>
</div>
<h2 className="font-headline-lg-mobile text-headline-lg-mobile text-black">Dimensional Analysis &amp; Unit Conversions</h2>
</div>
<div className="shrink-0 flex items-center justify-center w-12 h-12 bg-surface-container rounded-full text-secondary">
<span className="material-symbols-outlined text-2xl">straighten</span>
</div>
</div>
<div className="ml-3 mb-6">
<p className="font-body-md text-body-md text-black mb-4">
              Students are consistently multiplying when they should be dividing during cross-metric conversions. This 15-minute intervention uses a visual scaffolding approach rather than pure algorithmic steps.
           </p>
{/* Content Preview Snippet */}
<div className="bg-surface-container-low p-4 rounded-lg relative overflow-hidden group-hover:bg-surface-container transition-colors">
<div className="absolute top-0 right-0 p-2 opacity-20">
<span className="material-symbols-outlined text-4xl text-black">auto_awesome</span>
</div>
<h4 className="font-title-md text-title-md text-black mb-2">Lesson Structure</h4>
<ul className="space-y-2 font-body-md text-body-md text-black">
<li className="flex gap-2 items-start"><span className="text-secondary">•</span> Visualizing the "size" of units (5 min)</li>
<li className="flex gap-2 items-start"><span className="text-secondary">•</span> The Fraction-Matching technique (5 min)</li>
<li className="flex gap-2 items-start"><span className="text-secondary">•</span> Guided Practice: 3 problems (5 min)</li>
</ul>
</div>
</div>
<div className="mt-auto ml-3 flex flex-wrap items-center gap-3 pt-4 border-t border-surface-variant/20">
<button className="bg-secondary text-black font-title-md text-title-md px-6 py-2 rounded-lg hover:bg-secondary-fixed-dim transition-colors shadow-md flex items-center gap-2">
<span className="material-symbols-outlined text-[20px]">check_circle</span> Approve &amp; Schedule
          </button>
<button className="bg-transparent border border-surface-tint text-black font-title-md text-title-md px-4 py-2 rounded-lg hover:bg-surface-tint/5 transition-colors flex items-center gap-2">
<span className="material-symbols-outlined text-secondary text-[20px]">edit</span> Edit
          </button>
<div className="flex-1"></div>
<button className="text-black hover:text-error transition-colors flex items-center gap-1 font-label-sm text-label-sm">
<span className="material-symbols-outlined text-secondary text-[18px]">close</span> Dismiss
          </button>
</div>
</div>
{/* Card 2 */}
<div className="relative bg-surface-container-lowest rounded-xl p-card-padding shadow-[0_4px_40px_rgba(0,0,0,0.03)] overflow-hidden flex flex-col transition-transform duration-300 hover:-translate-y-1">
<div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
<div>
<div className="flex items-center gap-2 mb-1">
<span className="bg-tertiary-fixed text-black px-2 py-0.5 rounded text-[11px] font-label-sm tracking-widest uppercase">Medium Priority</span>
<span className="text-label-sm font-label-sm text-black">Affects 8 Students</span>
</div>
<h2 className="font-headline-lg-mobile text-headline-lg-mobile text-black">Newton's Third Law: Action/Reaction Pairs</h2>
</div>
<div className="shrink-0 flex items-center justify-center w-12 h-12 bg-surface-container rounded-full text-secondary">
<span className="material-symbols-outlined text-2xl">compare_arrows</span>
</div>
</div>
<div className="mb-6">
<p className="font-body-md text-body-md text-black mb-4">
              Confusion remains between action/reaction pairs acting on different objects vs. forces acting on the same object. This intervention uses real-world physics simulation examples.
           </p>
<div className="bg-surface-container-low p-4 rounded-lg relative overflow-hidden">
<h4 className="font-title-md text-title-md text-black mb-2">Included Resources</h4>
<div className="flex gap-3">
<span className="flex items-center gap-1 text-sm text-black bg-surface-container px-2 py-1 rounded"><span className="material-symbols-outlined text-secondary text-[16px]">movie</span> 1 Video</span>
<span className="flex items-center gap-1 text-sm text-black bg-surface-container px-2 py-1 rounded"><span className="material-symbols-outlined text-secondary text-[16px]">quiz</span> 5 Concept Questions</span>
</div>
</div>
</div>
<div className="mt-auto flex flex-wrap items-center gap-3 pt-4 border-t border-surface-variant/20">
<button className="bg-surface-container-highest text-black font-title-md text-title-md px-6 py-2 rounded-lg hover:bg-surface-variant transition-colors flex items-center gap-2">
<span className="material-symbols-outlined text-[20px]">check_circle</span> Approve
          </button>
<button className="bg-transparent border border-surface-tint text-black font-title-md text-title-md px-4 py-2 rounded-lg hover:bg-surface-tint/5 transition-colors flex items-center gap-2">
<span className="material-symbols-outlined text-secondary text-[20px]">edit</span> Edit
          </button>
<div className="flex-1"></div>
<button className="text-black hover:text-error transition-colors flex items-center gap-1 font-label-sm text-label-sm">
<span className="material-symbols-outlined text-secondary text-[18px]">close</span> Dismiss
          </button>
</div>
</div>
</div>
{/* Sidebar / Stats */}
<div className="lg:col-span-4 flex flex-col gap-6">
<div className="bg-surface-container rounded-xl p-card-padding shadow-sm">
<h3 className="font-title-md text-title-md text-black mb-6">Impact Summary</h3>
<div className="space-y-6">
{/* Metric 1 */}
<div>
<div className="flex justify-between text-label-sm font-label-sm text-black mb-1">
<span className="">Students Reached</span>
<span className="text-black font-bold">22</span>
</div>
<div className="w-full bg-surface-variant rounded-full h-1.5 overflow-hidden">
<div className="bg-surface-tint h-full rounded-full" style={{ width: '65%' }}></div>
</div>
</div>
{/* Metric 2 */}
<div>
<div className="flex justify-between text-label-sm font-label-sm text-black mb-1">
<span className="">Topics Addressed</span>
<span className="text-black font-bold">2 / 5</span>
</div>
<div className="w-full bg-surface-variant rounded-full h-1.5 overflow-hidden flex gap-0.5">
<div className="bg-secondary h-full rounded-full flex-1"></div>
<div className="bg-secondary h-full rounded-full flex-1"></div>
<div className="bg-surface-container-highest h-full rounded-full flex-1"></div>
<div className="bg-surface-container-highest h-full rounded-full flex-1"></div>
<div className="bg-surface-container-highest h-full rounded-full flex-1"></div>
</div>
</div>
</div>
<div className="mt-8 pt-6 border-t border-surface-variant/20">
<div className="flex items-start gap-3 bg-primary/5 p-4 rounded-lg">
<span className="material-symbols-outlined text-secondary mt-0.5">lightbulb</span>
<p className="font-body-md text-body-md text-black text-sm">
                   Approving interventions within 24 hours of detection increases concept retention by an estimated 18%.
                </p>
</div>
</div>
</div>
</div>
</div>
</div></main></div>

    </>
  );
}
