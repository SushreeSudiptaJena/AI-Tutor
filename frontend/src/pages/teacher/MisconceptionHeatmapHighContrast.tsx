/**
 * Converted from stitch_ascent_educator_dashboard/misconception_heatmap_high_contrast/misconception_heatmap_high_contrast.html
 */
export default function MisconceptionHeatmapHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-on-secondary -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-[#FFFFFF] tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-secondary-container font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="dashboard" href="#"><span className="material-symbols-outlined">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="my-classes" href="#"><span className="material-symbols-outlined">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="students" href="#"><span className="material-symbols-outlined">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="attendance" href="#"><span className="material-symbols-outlined">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="lesson-plans" href="#"><span className="material-symbols-outlined">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="assignments" href="#"><span className="material-symbols-outlined">assignment</span>Assignments</a><div className="my-4 border-t border-[#FFFFFF]/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-[#FFFFFF] uppercase tracking-widest">AI Insights</div><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-[#FFFFFF] font-semibold border-l-4 border-secondary" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined text-secondary">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="gap-map" href="#"><span className="material-symbols-outlined">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="tracking" href="#"><span className="material-symbols-outlined">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3 text-[#FFFFFF]" data-path="content-verification" href="#"><span className="material-symbols-outlined">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/5 hover:text-[#FFFFFF] transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-[#FFFFFF]/10 rounded-full px-6 py-2 flex items-center gap-3 border border-[#FFFFFF]/20 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-[#FFFFFF]">search</span><input className="bg-transparent border-none outline-none text-[#FFFFFF] w-full font-body-md placeholder-[#FFFFFF]" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-[#FFFFFF] hover:text-[#F5F5F5] transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-[#FFFFFF]/20"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-[#FFFFFF]">Dr. Sarah Ascent</div><div className="text-label-sm text-[#FFFFFF]">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-[#FFFFFF]"><div className="flex flex-col w-full relative min-h-[800px] font-body-md text-[#FFFFFF] p-6 gap-12">
{/* Header Section: Typographic Alignment & High Contrast */}
<header className="flex flex-col md:flex-row justify-between items-end gap-6 relative z-10 border-b border-[#FFFFFF]/20 pb-8">
<div className="flex flex-col max-w-2xl">
<span className="font-label-sm text-label-sm uppercase tracking-[0.2em] text-[#FFFFFF] mb-4 flex items-center gap-2">
<span className="material-symbols-outlined text-[16px] text-secondary">thermostat</span>
                Cognitive Analytics
            </span>
<h1 className="font-display-lg text-display-lg text-[#FFFFFF] m-0 leading-tight">
                Misconception Heatmap
            </h1>
<p className="font-body-lg text-body-lg text-[#FFFFFF] mt-4 max-w-xl">
                Identifying recurring flawed mental models in student reasoning paths. High-impact areas are highlighted for targeted reteaching interventions.
            </p>
</div>
<div className="flex items-center gap-4">
<div className="flex flex-col text-right">
<span className="font-title-md text-title-md text-[#FFFFFF]">Class: Alg II-B</span>
<span className="font-label-sm text-label-sm text-[#FFFFFF]">Last updated: 2h ago</span>
</div>
<button className="bg-secondary text-[#1A1A1A] px-6 py-3 rounded-lg font-title-md text-title-md hover:bg-secondary-fixed transition-colors shadow-sm flex items-center gap-2">
<span className="material-symbols-outlined">download</span> Export Data
             </button>
</div>
</header>
{/* Main Content Area: Floating Cream Cards */}
<div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative z-10">
{/* Left Column: Context & Summary Metrics */}
<div className="lg:col-span-4 flex flex-col gap-6">
<div className="bg-tertiary-fixed text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)] relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
<div className="absolute -right-12 -top-12 w-40 h-40 bg-secondary/10 rounded-full blur-2xl group-hover:bg-secondary/20 transition-colors"></div>
<h3 className="font-title-md text-title-md mb-6 pb-4 border-b border-tertiary-fixed-dim/50 flex justify-between items-center text-[#1A1A1A]">
                    Primary Intervention Target
                    <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: '\'FILL\' 1' }}>warning</span>
</h3>
<div className="flex flex-col gap-2">
<span className="font-display-lg text-display-lg text-[#1A1A1A]">45%</span>
<span className="font-body-md text-body-md text-[#1A1A1A]">of students consistently demonstrated flawed reasoning in:</span>
<strong className="font-title-md text-title-md mt-2 text-[#1A1A1A]">Fractional Division Scaling</strong>
</div>
<button className="mt-8 w-full border border-primary text-[#1A1A1A] px-4 py-3 rounded-lg font-title-md text-title-md hover:bg-primary/5 transition-colors flex items-center justify-center gap-2">
                    View Affected Students <span className="material-symbols-outlined text-[20px] text-secondary">arrow_forward</span>
</button>
</div>
<div className="bg-surface-container-lowest text-[#1A1A1A] p-8 rounded-2xl shadow-[0_4px_40px_rgba(0,0,0,0.05)]">
<h3 className="font-title-md text-title-md mb-6 pb-4 border-b border-[#1A1A1A]/20 text-[#1A1A1A]">Overall Impact Distribution</h3>
<div className="flex flex-col gap-5">
{/* Distribution Bar 1 */}
<div className="flex flex-col gap-1">
<div className="flex justify-between font-label-sm text-label-sm">
<span className="text-[#1A1A1A] font-semibold">Critical Impact (Requires Immediate Reteach)</span>
<span className="text-[#1A1A1A]">3</span>
</div>
<div className="w-full bg-[#1A1A1A]/10 h-2 rounded-full overflow-hidden">
<div className="bg-error h-full rounded-full w-[35%] relative">
<div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20"></div>
</div>
</div>
</div>
{/* Distribution Bar 2 */}
<div className="flex flex-col gap-1">
<div className="flex justify-between font-label-sm text-label-sm">
<span className="text-[#1A1A1A] font-semibold">Moderate Impact (Address in Review)</span>
<span className="text-[#1A1A1A]">5</span>
</div>
<div className="w-full bg-[#1A1A1A]/10 h-2 rounded-full overflow-hidden">
<div className="bg-secondary h-full rounded-full w-[45%]"></div>
</div>
</div>
{/* Distribution Bar 3 */}
<div className="flex flex-col gap-1">
<div className="flex justify-between font-label-sm text-label-sm">
<span className="text-[#1A1A1A] font-semibold">Low Impact (Monitor)</span>
<span className="text-[#1A1A1A]">8</span>
</div>
<div className="w-full bg-[#1A1A1A]/10 h-2 rounded-full overflow-hidden">
<div className="bg-outline-variant h-full rounded-full w-[20%]"></div>
</div>
</div>
</div>
</div>
{/* Decorative Visual Context */}
<div className="rounded-2xl overflow-hidden h-48 relative shadow-md group">
<div className="absolute inset-0 bg-surface-tint/20 mix-blend-multiply z-10 group-hover:bg-transparent transition-colors duration-500"></div>
<div className="w-full h-full bg-cover bg-center transition-transform duration-700 group-hover:scale-105" data-alt="A stylized, top-down view of a complex maze or intricate pathway system, rendered in soft cream and deep slate tones, with subtle gold accents highlighting incorrect turns or dead ends, visually representing cognitive missteps in a sophisticated, abstract way. Soft, diffused lighting." style={{ backgroundImage: 'url(\'https://lh3.googleusercontent.com/aida-public/AB6AXuAXVkY-QQJYlXH8LGI975-e00wn38x2J9k7gRi44_8uok-RkAq9ljDOMbBSgAkegsmZ0_B7m--RsMbQMGTDZiXGlMw_izPlHFyswE54RzGDPHX3_d8jwJPxtg8n64HyRv4XG6-8GO2HGhFnqqusJewC0O9uIkxJH6fUNd-DNJPJb44qATlN5s0wnpZYJgQ8DKKHePBM4aqiFpGVRqt8FPvguR_fegAi_K67HPHi_qzAcR6rZNRKh17B\')' }}></div>
</div>
</div>
{/* Right Column: The Heatmap Table */}
<div className="lg:col-span-8 flex flex-col">
<div className="bg-tertiary-fixed text-[#1A1A1A] rounded-2xl shadow-[0_8px_60px_rgba(0,0,0,0.08)] overflow-hidden flex flex-col h-full">
{/* Table Header */}
<div className="px-8 py-6 border-b border-tertiary-fixed-dim bg-tertiary-fixed-dim/20 flex items-center justify-between">
<h2 className="font-headline-lg text-headline-lg text-[#1A1A1A]">Identified Mental Models</h2>
<div className="flex items-center gap-3 bg-surface-container-lowest/50 px-4 py-2 rounded-full border border-outline-variant/30">
<span className="material-symbols-outlined text-outline text-[18px]">filter_list</span>
<span className="font-label-sm text-label-sm text-[#1A1A1A]">Sort by: Frequency (Desc)</span>
</div>
</div>
{/* Table Body List */}
<div className="flex flex-col divide-y divide-tertiary-fixed-dim/40 overflow-y-auto">
{/* Row 1: High Impact */}
<div className="px-8 py-6 hover:bg-tertiary-fixed-dim/10 transition-colors group relative flex flex-col md:flex-row gap-6 items-start md:items-center">
<div className="absolute left-0 top-0 bottom-0 w-1 bg-error opacity-100 group-hover:w-2 transition-all"></div>
<div className="flex-1 flex flex-col gap-2 min-w-0 pr-4">
<div className="flex items-center gap-3">
<span className="bg-error-container text-[#1A1A1A] font-label-sm text-label-sm px-2 py-1 rounded font-semibold">CRITICAL</span>
<h4 className="font-title-md text-title-md truncate text-[#1A1A1A]">Treats division as always shrinking the number</h4>
</div>
<p className="font-body-md text-body-md text-[#1A1A1A] line-clamp-2">
                                Students fail to recognize that dividing by a fraction less than 1 results in a quotient larger than the dividend. They apply whole-number heuristics inappropriately.
                            </p>
</div>
<div className="flex items-center gap-8 shrink-0">
<div className="flex flex-col items-end">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Frequency</span>
<span className="font-headline-lg text-headline-lg text-[#1A1A1A]">45%</span>
</div>
<button className="w-10 h-10 rounded-full border border-tertiary-fixed-dim flex items-center justify-center hover:bg-surface-container-lowest transition-colors text-[#1A1A1A] group-hover:border-secondary">
<span className="material-symbols-outlined text-secondary">chevron_right</span>
</button>
</div>
</div>
{/* Row 2: High Impact */}
<div className="px-8 py-6 hover:bg-tertiary-fixed-dim/10 transition-colors group relative flex flex-col md:flex-row gap-6 items-start md:items-center">
<div className="absolute left-0 top-0 bottom-0 w-1 bg-secondary opacity-100 group-hover:w-2 transition-all"></div>
<div className="flex-1 flex flex-col gap-2 min-w-0 pr-4">
<div className="flex items-center gap-3">
<span className="bg-secondary-container text-[#1A1A1A] font-label-sm text-label-sm px-2 py-1 rounded font-semibold">HIGH</span>
<h4 className="font-title-md text-title-md truncate text-[#1A1A1A]">Confusing area scaling with linear scaling</h4>
</div>
<p className="font-body-md text-body-md text-[#1A1A1A] line-clamp-2">
                                When a shape's dimensions are doubled, students assume the area is also doubled (x2) rather than quadrupled (x^2). Indicates weak grasp of dimensional growth.
                            </p>
</div>
<div className="flex items-center gap-8 shrink-0">
<div className="flex flex-col items-end">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Frequency</span>
<span className="font-headline-lg text-headline-lg text-[#1A1A1A]">38%</span>
</div>
<button className="w-10 h-10 rounded-full border border-tertiary-fixed-dim flex items-center justify-center hover:bg-surface-container-lowest transition-colors text-[#1A1A1A] group-hover:border-secondary">
<span className="material-symbols-outlined text-secondary">chevron_right</span>
</button>
</div>
</div>
{/* Row 3: Moderate Impact */}
<div className="px-8 py-6 hover:bg-tertiary-fixed-dim/10 transition-colors group relative flex flex-col md:flex-row gap-6 items-start md:items-center">
<div className="absolute left-0 top-0 bottom-0 w-1 bg-outline-variant opacity-0 group-hover:opacity-100 transition-all"></div>
<div className="flex-1 flex flex-col gap-2 min-w-0 pr-4">
<div className="flex items-center gap-3">
<span className="bg-surface-variant text-[#1A1A1A] font-label-sm text-label-sm px-2 py-1 rounded font-semibold">MODERATE</span>
<h4 className="font-title-md text-title-md truncate text-[#1A1A1A]">Misaligning decimal places in addition</h4>
</div>
<p className="font-body-md text-body-md text-[#1A1A1A] line-clamp-2">
                                Aligning numbers right-justified as if they were whole numbers, ignoring the decimal point position during vertical addition setups.
                            </p>
</div>
<div className="flex items-center gap-8 shrink-0">
<div className="flex flex-col items-end">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Frequency</span>
<span className="font-headline-lg text-headline-lg text-[#1A1A1A]">22%</span>
</div>
<button className="w-10 h-10 rounded-full border border-tertiary-fixed-dim flex items-center justify-center hover:bg-surface-container-lowest transition-colors text-[#1A1A1A] group-hover:border-secondary">
<span className="material-symbols-outlined text-secondary">chevron_right</span>
</button>
</div>
</div>
{/* Row 4: Low Impact */}
<div className="px-8 py-6 hover:bg-tertiary-fixed-dim/10 transition-colors group relative flex flex-col md:flex-row gap-6 items-start md:items-center opacity-80 hover:opacity-100">
<div className="absolute left-0 top-0 bottom-0 w-1 bg-outline-variant opacity-0 group-hover:opacity-100 transition-all"></div>
<div className="flex-1 flex flex-col gap-2 min-w-0 pr-4">
<div className="flex items-center gap-3">
<span className="bg-surface-variant text-[#1A1A1A] font-label-sm text-label-sm px-2 py-1 rounded font-semibold">LOW</span>
<h4 className="font-title-md text-title-md truncate text-[#1A1A1A]">Sign error in subtraction of negatives</h4>
</div>
<p className="font-body-md text-body-md text-[#1A1A1A] line-clamp-2">
                                Sporadic errors where subtracting a negative is treated as subtracting a positive, usually in multi-step equations rather than isolated problems.
                            </p>
</div>
<div className="flex items-center gap-8 shrink-0">
<div className="flex flex-col items-end">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Frequency</span>
<span className="font-headline-lg text-headline-lg text-[#1A1A1A]">12%</span>
</div>
<button className="w-10 h-10 rounded-full border border-tertiary-fixed-dim flex items-center justify-center hover:bg-surface-container-lowest transition-colors text-[#1A1A1A] group-hover:border-secondary">
<span className="material-symbols-outlined text-secondary">chevron_right</span>
</button>
</div>
</div>
</div>
{/* Table Footer */}
<div className="px-8 py-4 border-t border-tertiary-fixed-dim bg-tertiary-fixed-dim/10 flex justify-center mt-auto">
<button className="font-label-sm text-label-sm uppercase tracking-widest text-[#1A1A1A] hover:text-[#000000] transition-colors py-2 flex items-center gap-2">
                        Load More Entries <span className="material-symbols-outlined text-[16px] text-secondary">expand_more</span>
</button>
</div>
</div>
</div>
</div>
</div></main></div>

    </>
  );
}
