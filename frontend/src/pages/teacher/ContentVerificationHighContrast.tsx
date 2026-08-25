/**
 * Converted from stitch_ascent_educator_dashboard/content_verification_high_contrast/content_verification_high_contrast.html
 */
export default function ContentVerificationHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-white -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="dashboard" href="#"><span className="material-symbols-outlined text-secondary">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="my-classes" href="#"><span className="material-symbols-outlined text-secondary">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="students" href="#"><span className="material-symbols-outlined text-secondary">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="attendance" href="#"><span className="material-symbols-outlined text-secondary">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="lesson-plans" href="#"><span className="material-symbols-outlined text-secondary">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="assignments" href="#"><span className="material-symbols-outlined text-secondary">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined text-secondary">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined text-secondary">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="gap-map" href="#"><span className="material-symbols-outlined text-secondary">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined text-secondary">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="tracking" href="#"><span className="material-symbols-outlined text-secondary">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined text-secondary">psychology</span>Reteach</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="content-verification" href="#"><span className="material-symbols-outlined text-secondary">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined text-secondary">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-white">search</span><input className="bg-transparent border-none outline-none text-white w-full font-body-md" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-white hover:text-white transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-white">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full h-full relative group">
<div className="mb-12">
<div className="flex items-end justify-between flex-wrap gap-6 mb-4">
<div>
<h1 className="font-display-lg text-display-lg text-white mb-2 tracking-tight">Content Verification</h1>
<p className="font-body-lg text-body-lg text-white max-w-2xl">Review and moderate AI-sourced web materials before they become available in lesson plans and student assignments.</p>
</div>
<div className="flex gap-4">
<div className="flex flex-col items-end">
<span className="font-label-sm text-label-sm text-white uppercase tracking-widest mb-1">Queue Status</span>
<div className="flex items-center gap-2">
<span className="relative flex h-3 w-3">
<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-secondary opacity-75"></span>
<span className="relative inline-flex rounded-full h-3 w-3 bg-secondary"></span>
</span>
<span className="font-title-md text-title-md text-white">12 Items Pending</span>
</div>
</div>
</div>
</div>
<div className="h-1 w-full bg-surface-variant rounded-full overflow-hidden">
<div className="h-full bg-secondary w-1/4 rounded-full"></div>
</div>
</div>
<div className="flex flex-col gap-6">
<div className="flex items-center justify-between pb-4">
<div className="flex gap-4">
<button className="px-6 py-2 rounded-full bg-primary text-white font-label-sm text-label-sm tracking-wide uppercase transition-all shadow-md">All Pending</button>
<button className="px-6 py-2 rounded-full bg-surface text-black font-label-sm text-label-sm tracking-wide uppercase hover:bg-surface-container-high transition-all">High Priority</button>
<button className="px-6 py-2 rounded-full bg-surface text-black font-label-sm text-label-sm tracking-wide uppercase hover:bg-surface-container-high transition-all">Flagged Sources</button>
</div>
<div className="flex items-center gap-2 text-white font-label-sm text-label-sm">
<span className="material-symbols-outlined text-[18px]">sort</span>
<span className="">Sort: Oldest First</span>
</div>
</div>
<div className="bg-surface-container rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow relative overflow-hidden group">
<div className="absolute top-0 left-0 w-2 h-full bg-secondary opacity-80"></div>
<div className="flex flex-col lg:flex-row gap-8 items-start lg:items-center">
<div className="flex-1 min-w-0">
<div className="flex items-center gap-3 mb-3">
<span className="material-symbols-outlined text-black">language</span>
<a className="font-label-sm text-label-sm hover:text-black transition-colors truncate text-black" href="#">science-daily.org/articles/quantum-mechanics-basics</a>
<span className="px-2 py-1 rounded-md bg-secondary/10 text-black font-label-sm text-[10px] uppercase tracking-widest ml-auto lg:ml-0">Physics</span>
</div>
<h3 className="font-title-md text-title-md text-black mb-2">Introduction to Quantum Superposition for High Schoolers</h3>
<p className="font-body-md text-body-md text-black line-clamp-3">
             "Quantum superposition is a fundamental principle of quantum mechanics that states that, much like waves in classical physics, any two (or more) quantum states can be added together ("superposed") and the result will be another valid quantum state..."
           </p>
</div>
<div className="flex flex-row lg:flex-col gap-3 w-full lg:w-auto shrink-0 justify-end mt-4 lg:mt-0">
<button className="flex-1 lg:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-surface text-black font-label-sm text-label-sm uppercase tracking-wider hover:bg-error/10 hover:text-error transition-colors">
<span className="material-symbols-outlined text-[20px]">close</span>
              Reject
            </button>
<button className="flex-1 lg:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary-container text-white font-label-sm text-label-sm uppercase tracking-wider hover:bg-primary hover:text-white transition-colors shadow-sm">
<span className="material-symbols-outlined text-[20px]">check</span>
              Approve
            </button>
</div>
</div>
</div>
<div className="bg-surface-container rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow relative overflow-hidden group">
<div className="absolute top-0 left-0 w-2 h-full bg-tertiary opacity-80"></div>
<div className="flex flex-col lg:flex-row gap-8 items-start lg:items-center">
<div className="flex-1 min-w-0">
<div className="flex items-center gap-3 mb-3">
<span className="material-symbols-outlined text-black">article</span>
<a className="font-label-sm text-label-sm hover:text-black transition-colors truncate text-black" href="#">history-archive.edu/documents/industrial-revolution-primary</a>
<span className="px-2 py-1 rounded-md bg-tertiary/10 text-black font-label-sm text-[10px] uppercase tracking-widest ml-auto lg:ml-0">History</span>
</div>
<h3 className="font-title-md text-title-md text-black mb-2">Primary Sources: The Textile Mills of Manchester (1830)</h3>
<p className="font-body-md text-body-md text-black line-clamp-3">
             Extracts from parliamentary reports detailing the working conditions in early textile mills. Note: Contains archaic language and descriptions of difficult working conditions that may require contextualization for younger students before discussion.
           </p>
<div className="mt-4 flex items-center gap-2 text-black font-label-sm text-label-sm font-semibold">
<span className="material-symbols-outlined text-error text-[16px]">warning</span>
             AI Flag: Potential sensitivity issue detected (working conditions/child labor).
           </div>
</div>
<div className="flex flex-row lg:flex-col gap-3 w-full lg:w-auto shrink-0 justify-end mt-4 lg:mt-0">
<button className="flex-1 lg:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-surface text-black font-label-sm text-label-sm uppercase tracking-wider hover:bg-error/10 hover:text-error transition-colors">
<span className="material-symbols-outlined text-[20px]">close</span>
              Reject
            </button>
<button className="flex-1 lg:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary-container text-white font-label-sm text-label-sm uppercase tracking-wider hover:bg-primary hover:text-white transition-colors shadow-sm">
<span className="material-symbols-outlined text-[20px]">check</span>
              Approve
            </button>
</div>
</div>
</div>
<div className="bg-surface-container rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow relative overflow-hidden group">
<div className="absolute top-0 left-0 w-2 h-full bg-secondary opacity-80"></div>
<div className="flex flex-col lg:flex-row gap-8 items-start lg:items-center">
<div className="flex-1 min-w-0">
<div className="flex items-center gap-3 mb-3">
<span className="material-symbols-outlined text-black">code</span>
<a className="font-label-sm text-label-sm hover:text-black transition-colors truncate text-black" href="#">math-viz.com/interactive/calculus-limits</a>
<span className="px-2 py-1 rounded-md bg-secondary/10 text-black font-label-sm text-[10px] uppercase tracking-widest ml-auto lg:ml-0">Mathematics</span>
</div>
<h3 className="font-title-md text-title-md text-black mb-2">Interactive Limit Calculator Widget</h3>
<p className="font-body-md text-body-md text-black line-clamp-3">
             An embeddable interactive tool allowing students to manipulate variables x and y to visually understand limits approaching infinity. Includes dynamic graphing capabilities built with WebGL.
           </p>
</div>
<div className="flex flex-row lg:flex-col gap-3 w-full lg:w-auto shrink-0 justify-end mt-4 lg:mt-0">
<button className="flex-1 lg:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-surface text-black font-label-sm text-label-sm uppercase tracking-wider hover:bg-error/10 hover:text-error transition-colors">
<span className="material-symbols-outlined text-[20px]">close</span>
              Reject
            </button>
<button className="flex-1 lg:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary-container text-white font-label-sm text-label-sm uppercase tracking-wider hover:bg-primary hover:text-white transition-colors shadow-sm">
<span className="material-symbols-outlined text-[20px]">check</span>
              Approve
            </button>
</div>
</div>
</div>
<div className="mt-8 flex justify-center">
<button className="flex items-center gap-2 px-8 py-3 rounded-full bg-surface-variant/20 text-white font-label-sm text-label-sm uppercase tracking-wider hover:bg-surface-variant/30 transition-colors">
        Load More Items <span className="material-symbols-outlined text-[18px]">expand_more</span>
</button>
</div>
</div>
</div></main></div>

    </>
  );
}
