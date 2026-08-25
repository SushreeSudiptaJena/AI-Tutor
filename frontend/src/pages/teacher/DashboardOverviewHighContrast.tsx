/**
 * Converted from stitch_ascent_educator_dashboard/dashboard_overview_high_contrast/dashboard_overview_high_contrast.html
 */
export default function DashboardOverviewHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-white -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="dashboard" href="#"><span className="material-symbols-outlined text-secondary">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="my-classes" href="#"><span className="material-symbols-outlined">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="students" href="#"><span className="material-symbols-outlined">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="attendance" href="#"><span className="material-symbols-outlined">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="lesson-plans" href="#"><span className="material-symbols-outlined">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="assignments" href="#"><span className="material-symbols-outlined">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="gap-map" href="#"><span className="material-symbols-outlined">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="tracking" href="#"><span className="material-symbols-outlined">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="content-verification" href="#"><span className="material-symbols-outlined">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-white">search</span><input className="bg-transparent border-none outline-none text-white w-full font-body-md placeholder-white/70" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-white transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-white">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full gap-gutter">
{/* Hero / Stats */}
<section className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
{/* Stat Card 1 */}
<div className="bg-surface-container-low rounded-xl p-card-padding shadow-md flex flex-col gap-4 relative overflow-hidden group">
<div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
<div className="flex justify-between items-start z-10">
<span className="text-[#1a1a1a] font-label-sm uppercase tracking-widest font-bold">Total Students</span>
<div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
<span className="material-symbols-outlined">groups</span>
</div>
</div>
<div className="text-display-lg text-[#1a1a1a] font-display-lg z-10">42</div>
<div className="text-label-sm text-[#1a1a1a] flex items-center gap-1 z-10 font-bold">
<span className="material-symbols-outlined text-[16px] text-secondary">trending_up</span>
<span className="">+2 from last term</span>
</div>
</div>
{/* Stat Card 2 */}
<div className="bg-surface-container-low rounded-xl p-card-padding shadow-md flex flex-col gap-4 relative overflow-hidden group">
<div className="absolute inset-0 bg-gradient-to-br from-secondary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
<div className="flex justify-between items-start z-10">
<span className="text-[#1a1a1a] font-label-sm uppercase tracking-widest font-bold">Avg. Mastery</span>
<div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center text-secondary">
<span className="material-symbols-outlined">donut_large</span>
</div>
</div>
<div className="flex items-end gap-2 z-10">
<div className="text-display-lg text-[#1a1a1a] font-display-lg">68<span className="text-headline-lg">%</span></div>
</div>
<div className="w-full h-1 bg-[#1a1a1a]/20 rounded-full z-10 mt-auto">
<div className="h-full bg-secondary rounded-full" style={{ width: '68%' }}></div>
</div>
</div>
{/* Stat Card 3 */}
<div className="bg-error-container rounded-xl p-card-padding shadow-md flex flex-col gap-4 relative overflow-hidden group">
<div className="flex justify-between items-start z-10">
<span className="text-[#1a1a1a] font-label-sm uppercase tracking-widest font-bold">Active Flags</span>
<div className="w-10 h-10 rounded-full bg-on-error-container/10 flex items-center justify-center text-on-error-container">
<span className="material-symbols-outlined">flag</span>
</div>
</div>
<div className="text-display-lg text-[#1a1a1a] font-display-lg z-10">8</div>
<div className="text-label-sm text-[#1a1a1a] flex items-center gap-1 z-10 font-bold">
<span className="">Requires attention today</span>
</div>
</div>
</section>
{/* Main Content Split */}
<section className="grid grid-cols-1 lg:grid-cols-12 gap-gutter">
{/* Left Column: Heatmap & Gaps (8 cols) */}
<div className="lg:col-span-8 flex flex-col gap-gutter">
{/* Concept Mastery Heatmap */}
<div className="bg-surface-container-low rounded-xl p-card-padding shadow-md flex flex-col gap-6">
<div className="flex justify-between items-end border-b-2 border-surface-container pb-4">
<div>
<h2 className="text-headline-lg font-headline-lg text-[#1a1a1a]">Concept Mastery</h2>
<p className="text-body-md text-[#1a1a1a] mt-1 font-bold">Class-wide performance across key modules</p>
</div>
<button className="text-[#1a1a1a] transition-colors font-label-sm uppercase tracking-wider flex items-center gap-1 font-bold">
                        View Details <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
</button>
</div>
<div className="grid grid-cols-4 gap-2">
{/* Heatmap Legend */}
<div className="col-span-4 flex justify-end items-center gap-4 text-label-sm text-[#1a1a1a] mb-2 font-bold">
<span className="">Needs Focus</span>
<div className="flex gap-1">
<div className="w-4 h-4 bg-error-container rounded-sm"></div>
<div className="w-4 h-4 bg-secondary-fixed/50 rounded-sm"></div>
<div className="w-4 h-4 bg-primary-fixed-dim rounded-sm"></div>
<div className="w-4 h-4 bg-primary-fixed rounded-sm"></div>
</div>
<span className="">Mastered</span>
</div>
{/* Row 1 */}
<div className="col-span-1 flex items-center justify-end pr-4 text-label-sm font-label-sm text-[#1a1a1a] font-bold">Fractions</div>
<div className="bg-primary-fixed rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        85%
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-inverse-surface text-white text-xs py-1 px-2 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-20">Unit 1: Basics</div>
</div>
<div className="bg-primary-fixed-dim rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        72%
                    </div>
<div className="bg-secondary-fixed/50 rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        60%
                    </div>
{/* Row 2 */}
<div className="col-span-1 flex items-center justify-end pr-4 text-label-sm font-label-sm text-[#1a1a1a] font-bold">Algebra</div>
<div className="bg-primary-fixed-dim rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        78%
                    </div>
<div className="bg-secondary-fixed/50 rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        55%
                    </div>
<div className="bg-error-container rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        33%
                    </div>
{/* Row 3 */}
<div className="col-span-1 flex items-center justify-end pr-4 text-label-sm font-label-sm text-[#1a1a1a] font-bold">Geometry</div>
<div className="bg-primary-fixed rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        90%
                    </div>
<div className="bg-primary-fixed-dim rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        82%
                    </div>
<div className="bg-primary-fixed rounded-md h-12 flex items-center justify-center text-[#1a1a1a] font-bold shadow-sm relative group cursor-pointer hover:scale-[1.02] transition-transform">
                        88%
                    </div>
</div>
</div>
{/* Top Learning Gaps */}
<div className="bg-surface-container-low rounded-xl p-card-padding shadow-md flex flex-col gap-6">
<div className="flex justify-between items-end border-b-2 border-surface-container pb-4">
<h2 className="text-title-md font-title-md text-[#1a1a1a]">Top Learning Gaps</h2>
<span className="text-label-sm text-[#1a1a1a] font-bold">Priority Focus Areas</span>
</div>
<div className="flex flex-col gap-3">
{/* Gap Item */}
<div className="flex items-center justify-between p-4 bg-surface rounded-lg border-l-4 border-error transition-colors cursor-pointer group">
<div className="flex flex-col gap-1">
<span className="font-bold text-[#1a1a1a] transition-colors">Quadratic Equations</span>
<span className="text-label-sm text-[#1a1a1a] font-bold">Algebra II • 15 students struggling</span>
</div>
<div className="flex items-center gap-3">
<span className="text-[#1a1a1a] font-bold text-lg">33%</span>
<span className="material-symbols-outlined text-[#1a1a1a] transition-colors">chevron_right</span>
</div>
</div>
{/* Gap Item */}
<div className="flex items-center justify-between p-4 bg-surface rounded-lg border-l-4 border-secondary transition-colors cursor-pointer group">
<div className="flex flex-col gap-1">
<span className="font-bold text-[#1a1a1a] transition-colors">Adding Unlike Fractions</span>
<span className="text-label-sm text-[#1a1a1a] font-bold">Fractions • 8 students struggling</span>
</div>
<div className="flex items-center gap-3">
<span className="text-[#1a1a1a] font-bold text-lg">60%</span>
<span className="material-symbols-outlined text-[#1a1a1a] transition-colors">chevron_right</span>
</div>
</div>
</div>
</div>
</div>
{/* Right Column: AI Insights & Flags (4 cols) */}
<div className="lg:col-span-4 flex flex-col gap-gutter">
{/* AI Insights Teaser */}
<div className="bg-primary rounded-xl p-card-padding shadow-lg text-white relative overflow-hidden flex flex-col min-h-[250px] justify-between group">
{/* Decorative element */}
<div className="absolute -right-12 -top-12 w-48 h-48 bg-secondary/10 rounded-full blur-2xl group-hover:bg-secondary/20 transition-all duration-500"></div>
<div className="z-10 flex flex-col gap-2">
<div className="flex items-center gap-2 mb-2">
<span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: '\'FILL\' 1' }}>auto_awesome</span>
<span className="font-label-sm text-white uppercase tracking-widest">Ascent AI</span>
</div>
<h3 className="text-headline-lg font-headline-lg leading-tight text-white">12 New Insights Found</h3>
<p className="text-body-md text-white mt-2">Analysis complete on recent Algebra quiz results. Patterns detected in factoring errors.</p>
</div>
<a className="z-10 mt-6 inline-flex items-center justify-center px-6 py-3 bg-secondary text-[#1a1a1a] font-bold rounded-lg transition-colors w-fit gap-2 shadow-md" href="#">
                    View All Insights <span className="material-symbols-outlined text-[20px]">explore</span>
</a>
</div>
{/* Recent Student Flags */}
<div className="bg-surface-container-low rounded-xl p-card-padding shadow-md flex flex-col gap-6 flex-1">
<div className="flex justify-between items-end border-b-2 border-surface-container pb-4">
<h2 className="text-title-md font-title-md text-[#1a1a1a]">Student Flags</h2>
<span className="w-6 h-6 rounded-full bg-error text-white flex items-center justify-center text-xs font-bold shadow-sm">8</span>
</div>
<div className="flex flex-col gap-4">
{/* Flag Item */}
<div className="flex items-start gap-3 group cursor-pointer">
<div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-[#1a1a1a] font-bold border border-[#1a1a1a]/10 shrink-0">
                            AS
                        </div>
<div className="flex flex-col gap-1 border-b border-[#1a1a1a]/10 pb-3 flex-1 transition-colors">
<div className="flex justify-between items-start">
<span className="font-bold text-[#1a1a1a] transition-colors">Aarav S.</span>
<span className="text-xs text-[#1a1a1a] font-bold">2h ago</span>
</div>
<div className="flex items-center gap-2">
<span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-error-container text-[#1a1a1a]">Low Engagement</span>
</div>
<span className="text-sm text-[#1a1a1a] font-bold mt-1 line-clamp-2">Missed 3 consecutive assignments in Geometry.</span>
</div>
</div>
{/* Flag Item */}
<div className="flex items-start gap-3 group cursor-pointer">
<div className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-[#1a1a1a] font-bold border border-[#1a1a1a]/10 shrink-0">
                            MJ
                        </div>
<div className="flex flex-col gap-1 border-b border-[#1a1a1a]/10 pb-3 flex-1 transition-colors">
<div className="flex justify-between items-start">
<span className="font-bold text-[#1a1a1a] transition-colors">Mia J.</span>
<span className="text-xs text-[#1a1a1a] font-bold">Yesterday</span>
</div>
<div className="flex items-center gap-2">
<span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-secondary-container text-[#1a1a1a]">Struggling</span>
</div>
<span className="text-sm text-[#1a1a1a] font-bold mt-1 line-clamp-2">Consistent errors in identifying slope-intercept form.</span>
</div>
</div>
</div>
<button className="mt-auto pt-4 text-sm font-bold text-[#1a1a1a] transition-colors text-center">
                    See All Flags
                </button>
</div>
</div>
</section>
{/* Layout Inspiration Image Container (Hidden visually, but present for data requirements) */}
<div className="hidden">
<img alt="Layout Inspiration" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAXzaKZlCaOiKn6rdic5T0pTyg7-lNrYl9epgYp2InJYSyEYUeRZmK5kqkVC-SlqjT9uJGlg5K_bPdxKk31fJQ7PPfLdqLBWy5enO3asCN_iJ1k8bE44cE1fnE-vKTkIOc0CaDgR_XHydtNdbVLHMtHScz_qxh1ava_EjO2HVNeMYF3043xWfzsKBq_DSEMxH1sHYfzbO6x_f8EpptDC-w3AHuJyJ5HSDwocTsDkvq3xNV-CPShk9zNe83B3dtqwqWfiw"/>
</div>
</div></main></div>

    </>
  );
}
