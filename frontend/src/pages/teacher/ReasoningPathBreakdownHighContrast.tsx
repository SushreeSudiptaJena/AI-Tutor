/**
 * Converted from stitch_ascent_educator_dashboard/reasoning_path_breakdown_high_contrast/reasoning_path_breakdown_high_contrast.html
 */
export default function ReasoningPathBreakdownHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-on-secondary -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="dashboard" href="#"><span className="material-symbols-outlined">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="my-classes" href="#"><span className="material-symbols-outlined">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="students" href="#"><span className="material-symbols-outlined">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="attendance" href="#"><span className="material-symbols-outlined">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="lesson-plans" href="#"><span className="material-symbols-outlined">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="assignments" href="#"><span className="material-symbols-outlined">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined">thermostat</span>Heatmap</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="gap-map" href="#"><span className="material-symbols-outlined">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="tracking" href="#"><span className="material-symbols-outlined">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="content-verification" href="#"><span className="material-symbols-outlined">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-[#f5f5f5]">search</span><input className="bg-transparent border-none outline-none text-[#f5f5f5] placeholder-[#f5f5f5] w-full font-body-md" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-[#f5f5f5] hover:text-white transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-[#f5f5f5]">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full relative">
{/* Decorative Ambient Backdrop */}
<div className="fixed inset-0 pointer-events-none opacity-20 z-0">
<div className="absolute top-20 right-20 w-96 h-96 bg-primary-fixed blur-3xl rounded-full"></div>
<div className="absolute bottom-20 left-20 w-80 h-80 bg-secondary-fixed blur-3xl rounded-full"></div>
</div>
<div className="relative z-10 flex flex-col gap-margin-desktop">
{/* Header Section */}
<header className="flex flex-col gap-6 pt-8">
<div className="flex items-center gap-4">
<span className="material-symbols-outlined text-headline-lg text-primary bg-primary-fixed/20 p-3 rounded-xl shadow-sm">route</span>
<div>
<h1 className="font-display-lg text-display-lg text-white">Reasoning Paths</h1>
<p className="font-body-lg text-body-lg text-[#f5f5f5] mt-2 max-w-2xl">
            Analyze the distinct cognitive routes your students took to reach their answers. 
            Identifying specific missteps allows for targeted reteaching.
          </p>
</div>
</div>
{/* Problem Selection Dropdown (Simulated) */}
<div className="relative max-w-3xl mt-6 group">
<label className="absolute -top-3 left-4 px-2 bg-surface text-label-sm font-label-sm text-[#1a1a1a] uppercase tracking-widest z-10 transition-colors group-focus-within:text-[#1a1a1a]">Selected Problem</label>
<div className="relative flex items-center bg-surface-container-lowest rounded-xl shadow-sm hover:shadow-md transition-shadow cursor-pointer p-4 group-focus-within:ring-2 ring-secondary/50">
<div className="w-12 h-12 bg-surface-variant rounded-lg flex items-center justify-center mr-4">
<span className="font-title-md text-title-md text-[#1a1a1a]">Q4</span>
</div>
<div className="flex-1">
<p className="font-body-md text-body-md text-[#1a1a1a] line-clamp-2">"A train leaves Chicago at 60mph. Another leaves St. Louis..." (Systems of Equations)</p>
</div>
<span className="material-symbols-outlined text-[#1a1a1a] ml-4">expand_more</span>
</div>
{/* Metrics for Selected Problem */}
<div className="flex gap-8 mt-6 px-4">
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-white uppercase tracking-widest">Total Attempts</span>
<span className="font-headline-lg text-headline-lg text-white">28</span>
</div>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-white uppercase tracking-widest">Common Errors</span>
<span className="font-headline-lg text-headline-lg text-white">3</span>
</div>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-white uppercase tracking-widest">Success Rate</span>
<span className="font-headline-lg text-headline-lg text-white">42%</span>
</div>
</div>
</div>
</header>
{/* Error Patterns List */}
<div className="flex flex-col gap-12 mt-8">
{/* Pattern 1 */}
<section className="relative">
{/* Connecting Path Line */}
<div className="absolute left-8 top-16 bottom-[-48px] w-0.5 bg-surface-variant/50 hidden md:block z-0"></div>
<div className="grid grid-cols-1 md:grid-cols-12 gap-8 relative z-10">
{/* Meta & Visuals */}
<div className="md:col-span-4 flex flex-col gap-4">
<div className="flex items-center gap-4">
<div className="w-16 h-16 bg-error-container rounded-full flex items-center justify-center shadow-sm relative shrink-0">
<span className="material-symbols-outlined text-[#1a1a1a] text-[32px]">conversion_path</span>
<div className="absolute -top-1 -right-1 bg-surface-container-lowest text-[#1a1a1a] font-label-sm text-label-sm px-2 py-0.5 rounded-full shadow-sm">45%</div>
</div>
<h3 className="font-headline-lg text-headline-lg text-white">Unit Confusion</h3>
</div>
<div className="pl-20 md:pl-0 pt-4">
<p className="font-body-md text-body-md text-[#f5f5f5]">
                  Students mixed up hours and minutes, multiplying speed by 90 (minutes) instead of 1.5 (hours).
                </p>
<div className="mt-6">
<span className="inline-flex items-center gap-2 bg-surface text-[#1a1a1a] px-4 py-2 rounded-full text-label-sm font-label-sm shadow-sm">
<span className="w-2 h-2 rounded-full bg-error"></span>
                      12 Students Affected
                    </span>
</div>
</div>
</div>
{/* Student Examples / Quotes */}
<div className="md:col-span-8 flex flex-col gap-6 pl-10 md:pl-0 border-l-2 border-error/20 md:border-none">
{/* Example Card */}
<div className="bg-surface-container-lowest rounded-2xl shadow-sm p-8 hover:-translate-y-1 transition-transform duration-300 relative overflow-hidden group">
<div className="absolute top-0 left-0 w-1 h-full bg-error/80 transition-all duration-300 group-hover:w-2"></div>
<span className="material-symbols-outlined absolute top-4 right-4 text-[#1a1a1a]/30 text-6xl rotate-180 -scale-y-100">format_quote</span>
<div className="flex items-center justify-between mb-6">
<span className="font-label-sm text-label-sm bg-surface-container px-3 py-1 rounded-full text-[#1a1a1a]">Student A (Anonymized)</span>
<button className="text-[#1a1a1a] hover:text-[#1a1a1a] transition-colors flex items-center gap-1 font-label-sm text-label-sm uppercase tracking-wider">
                   Full Work <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
</button>
</div>
<blockquote className="font-body-lg text-body-lg text-[#1a1a1a] italic relative z-10 leading-relaxed">
                 "I took the speed of 60 mph and multiplied it by the time they were traveling, which was <span className="bg-error-container/50 px-1 rounded-sm text-[#1a1a1a] font-semibold">90 minutes</span>. So 60 * 90 = 5400 miles."
               </blockquote>
<div className="mt-6 pt-4 border-t border-surface-variant/20 flex gap-4">
<div className="flex-1 bg-surface p-4 rounded-xl">
<div className="font-label-sm text-label-sm text-[#1a1a1a] uppercase tracking-widest mb-2">AI Diagnosis</div>
<p className="font-body-md text-body-md text-[#1a1a1a]">Failed to convert minutes to hours before applying the formula \( d = rt \).</p>
</div>
</div>
</div>
{/* Example Card */}
<div className="bg-surface-container-lowest rounded-2xl shadow-sm p-8 hover:-translate-y-1 transition-transform duration-300 relative overflow-hidden group opacity-80 scale-95 origin-top">
<div className="absolute top-0 left-0 w-1 h-full bg-error/50 transition-all duration-300 group-hover:w-2"></div>
<div className="flex items-center justify-between mb-4">
<span className="font-label-sm text-label-sm bg-surface-container px-3 py-1 rounded-full text-[#1a1a1a]">Student G</span>
</div>
<blockquote className="font-body-lg text-body-lg text-[#1a1a1a] italic relative z-10 line-clamp-2">
                 "If the time is 1 hour and 30 minutes, I just multiply 60 by <span className="bg-error-container/50 px-1 rounded-sm text-[#1a1a1a]">1.30</span>..."
               </blockquote>
</div>
</div>
</div>
</section>
{/* Pattern 2 */}
<section className="relative">
<div className="absolute left-8 top-16 bottom-[-48px] w-0.5 bg-surface-variant/50 hidden md:block z-0"></div>
<div className="grid grid-cols-1 md:grid-cols-12 gap-8 relative z-10">
<div className="md:col-span-4 flex flex-col gap-4">
<div className="flex items-center gap-4">
<div className="w-16 h-16 bg-secondary-container rounded-full flex items-center justify-center shadow-sm relative shrink-0">
<span className="material-symbols-outlined text-[#1a1a1a] text-[32px]">compare_arrows</span>
<div className="absolute -top-1 -right-1 bg-surface-container-lowest text-[#1a1a1a] font-label-sm text-label-sm px-2 py-0.5 rounded-full shadow-sm">25%</div>
</div>
<h3 className="font-headline-lg text-headline-lg text-white">Relative Velocity</h3>
</div>
<div className="pl-20 md:pl-0 pt-4">
<p className="font-body-md text-body-md text-[#f5f5f5]">
                  Students subtracted the speeds instead of adding them, misunderstanding that trains moving towards each other close the distance faster.
                </p>
<div className="mt-6">
<span className="inline-flex items-center gap-2 bg-surface text-[#1a1a1a] px-4 py-2 rounded-full text-label-sm font-label-sm shadow-sm">
<span className="w-2 h-2 rounded-full bg-secondary"></span>
                      7 Students Affected
                    </span>
</div>
</div>
</div>
<div className="md:col-span-8 flex flex-col gap-6 pl-10 md:pl-0 border-l-2 border-secondary/20 md:border-none">
<div className="bg-surface-container-lowest rounded-2xl shadow-sm p-8 hover:-translate-y-1 transition-transform duration-300 relative overflow-hidden group">
<div className="absolute top-0 left-0 w-1 h-full bg-secondary/80 transition-all duration-300 group-hover:w-2"></div>
<span className="material-symbols-outlined absolute top-4 right-4 text-[#1a1a1a]/30 text-6xl rotate-180 -scale-y-100">format_quote</span>
<div className="flex items-center justify-between mb-6">
<span className="font-label-sm text-label-sm bg-surface-container px-3 py-1 rounded-full text-[#1a1a1a]">Student M</span>
<button className="text-[#1a1a1a] hover:text-[#1a1a1a] transition-colors flex items-center gap-1 font-label-sm text-label-sm uppercase tracking-wider">
                   Full Work <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
</button>
</div>
<blockquote className="font-body-lg text-body-lg text-[#1a1a1a] italic relative z-10 leading-relaxed">
                 "Train A is 60mph and Train B is 45mph. To find how fast they are getting closer, I did <span className="bg-secondary-fixed/50 px-1 rounded-sm text-[#1a1a1a] font-semibold">60 - 45 = 15mph</span>."
               </blockquote>
<div className="mt-6 pt-4 border-t border-surface-variant/20 flex gap-4">
<div className="flex-1 bg-surface p-4 rounded-xl">
<div className="font-label-sm text-label-sm text-[#1a1a1a] uppercase tracking-widest mb-2">AI Diagnosis</div>
<p className="font-body-md text-body-md text-[#1a1a1a]">Conceptual error regarding relative motion in opposing directions.</p>
</div>
</div>
</div>
</div>
</div>
</section>
{/* Suggestion Action */}
<section className="mt-8 grid grid-cols-1 md:grid-cols-12 gap-8 relative z-10 pb-20">
<div className="md:col-span-4 flex items-end">
{/* Spacer to align with content */}
</div>
<div className="md:col-span-8">
<div className="bg-primary text-white p-8 rounded-2xl shadow-xl flex items-center justify-between gap-8 relative overflow-hidden group cursor-pointer hover:bg-primary-container transition-colors">
<div className="absolute top-0 right-0 w-64 h-64 bg-secondary/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 group-hover:scale-150 transition-transform duration-700"></div>
<div className="flex-1 relative z-10">
<h4 className="font-title-md text-title-md text-white mb-2">Generate Reteach Materials</h4>
<p className="font-body-md text-body-md text-[#f5f5f5]">
                   Create a targeted mini-lesson addressing Unit Conversion and Relative Velocity.
                 </p>
</div>
<div className="w-14 h-14 bg-secondary rounded-full flex items-center justify-center shadow-lg relative z-10 shrink-0 group-hover:rotate-12 transition-transform">
<span className="material-symbols-outlined text-[#1a1a1a] text-2xl">auto_awesome</span>
</div>
</div>
</div>
</section>
</div>
</div>
</div></main></div>

    </>
  );
}
