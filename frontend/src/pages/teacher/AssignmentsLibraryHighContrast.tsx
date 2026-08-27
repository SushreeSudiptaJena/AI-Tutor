/**
 * Converted from stitch_ascent_educator_dashboard/assignments_library_high_contrast/assignments_library_high_contrast.html
 */
export default function AssignmentsLibraryHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-white -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="dashboard" href="#"><span className="material-symbols-outlined">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="my-classes" href="#"><span className="material-symbols-outlined">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="students" href="#"><span className="material-symbols-outlined">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="attendance" href="#"><span className="material-symbols-outlined">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="lesson-plans" href="#"><span className="material-symbols-outlined">auto_stories</span>Lesson Plans</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="assignments" href="#"><span className="material-symbols-outlined">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="gap-map" href="#"><span className="material-symbols-outlined">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="tracking" href="#"><span className="material-symbols-outlined">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="content-verification" href="#"><span className="material-symbols-outlined">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-[36rem] bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-white">search</span><input className="bg-transparent border-none outline-none text-white placeholder:text-white w-full font-body-md" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-white hover:text-white transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-white">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full relative">
<div className="flex items-center justify-between mb-margin-desktop">
<div>
<h1 className="font-display-lg text-display-lg text-white mb-2">Assignments Library</h1>
<p className="font-body-md text-body-md text-white max-w-2xl">Manage your distributed worksheets, exams, and matching answer keys.</p>
</div>
<button className="bg-secondary text-white px-6 py-3 rounded-full font-title-md text-title-md shadow-md hover:shadow-lg transition-shadow flex items-center gap-2">
<span className="material-symbols-outlined">add</span>
            Create New Assignment
        </button>
</div>
<div className="w-full relative mb-12">
<div className="flex gap-8 border-b border-surface-variant/20 relative" id="tabContainer">
<button className="tab-btn active pb-4 font-title-md text-title-md text-white transition-colors relative" data-target="questionsTab">
                Questions
                <div className="absolute bottom-0 left-0 w-full h-1 bg-secondary rounded-t-full transition-transform origin-left duration-300 tab-indicator"></div>
</button>
<button className="tab-btn pb-4 font-title-md text-title-md text-white hover:text-white transition-colors relative" data-target="answerKeysTab">
                Answer Keys
                <div className="absolute bottom-0 left-0 w-full h-1 bg-secondary rounded-t-full transition-transform origin-left duration-300 scale-x-0 tab-indicator"></div>
</button>
</div>
</div>
<div className="relative w-full overflow-hidden min-h-[500px]">
<div className="tab-content absolute inset-0 w-full transition-all duration-500 opacity-100 translate-x-0" id="questionsTab">
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
<div className="bg-surface-container rounded-xl p-6 shadow-sm hover:shadow-md transition-all group flex flex-col h-full relative overflow-hidden">
<div className="absolute top-0 right-0 w-24 h-24 bg-primary-container rounded-bl-full opacity-10 -z-10 group-hover:scale-110 transition-transform"></div>
<div className="flex justify-between items-start mb-6">
<div className="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center text-primary">
<span className="material-symbols-outlined text-[28px]">description</span>
</div>
<div className="bg-secondary text-white px-3 py-1 rounded-full font-label-sm text-label-sm">Active</div>
</div>
<h3 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-2 line-clamp-2">Cellular Respiration Quiz</h3>
<p className="font-body-sm text-body-md text-[#1A1A1A] mb-6 flex items-center gap-2">
<span className="material-symbols-outlined text-[16px]">calendar_today</span>
                        Due: Oct 15, 2024
                    </p>
<div className="mt-auto pt-6 border-t border-surface-variant/10 flex justify-between items-center">
<div>
<span className="font-title-md text-title-md text-[#1A1A1A]">24/30</span>
<span className="font-body-md text-body-md text-[#1A1A1A] ml-1">Submissions</span>
</div>
<button className="w-10 h-10 rounded-full bg-surface-variant/20 hover:bg-primary hover:text-white transition-colors flex items-center justify-center text-[#1A1A1A]">
<span className="material-symbols-outlined">more_vert</span>
</button>
</div>
</div>
<div className="bg-surface-container rounded-xl p-6 shadow-sm hover:shadow-md transition-all group flex flex-col h-full relative overflow-hidden">
<div className="absolute top-0 right-0 w-24 h-24 bg-primary-container rounded-bl-full opacity-10 -z-10 group-hover:scale-110 transition-transform"></div>
<div className="flex justify-between items-start mb-6">
<div className="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center text-primary">
<span className="material-symbols-outlined text-[28px]">description</span>
</div>
<div className="bg-secondary text-white px-3 py-1 rounded-full font-label-sm text-label-sm">Active</div>
</div>
<h3 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-2 line-clamp-2">Mitosis vs Meiosis Worksheet</h3>
<p className="font-body-sm text-body-md text-[#1A1A1A] mb-6 flex items-center gap-2">
<span className="material-symbols-outlined text-[16px]">calendar_today</span>
                        Due: Oct 18, 2024
                    </p>
<div className="mt-auto pt-6 border-t border-surface-variant/10 flex justify-between items-center">
<div>
<span className="font-title-md text-title-md text-[#1A1A1A]">5/30</span>
<span className="font-body-md text-body-md text-[#1A1A1A] ml-1">Submissions</span>
</div>
<button className="w-10 h-10 rounded-full bg-surface-variant/20 hover:bg-primary hover:text-white transition-colors flex items-center justify-center text-[#1A1A1A]">
<span className="material-symbols-outlined">more_vert</span>
</button>
</div>
</div>
<div className="bg-surface-container rounded-xl p-6 shadow-sm hover:shadow-md transition-all group flex flex-col h-full relative overflow-hidden">
<div className="absolute top-0 right-0 w-24 h-24 bg-surface-variant rounded-bl-full opacity-20 -z-10 group-hover:scale-110 transition-transform"></div>
<div className="flex justify-between items-start mb-6">
<div className="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center text-surface-variant">
<span className="material-symbols-outlined text-[28px]">description</span>
</div>
<div className="bg-inverse-surface text-white px-3 py-1 rounded-full font-label-sm text-label-sm">Closed</div>
</div>
<h3 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-2 line-clamp-2">DNA Replication Lab Report</h3>
<p className="font-body-sm text-body-md text-[#1A1A1A] mb-6 flex items-center gap-2">
<span className="material-symbols-outlined text-[16px]">calendar_today</span>
                        Due: Sep 30, 2024
                    </p>
<div className="mt-auto pt-6 border-t border-surface-variant/10 flex justify-between items-center">
<div>
<span className="font-title-md text-title-md text-[#1A1A1A]">30/30</span>
<span className="font-body-md text-body-md text-[#1A1A1A] ml-1">Submissions</span>
</div>
<button className="w-10 h-10 rounded-full bg-surface-variant/20 hover:bg-primary hover:text-white transition-colors flex items-center justify-center text-[#1A1A1A]">
<span className="material-symbols-outlined">more_vert</span>
</button>
</div>
</div>
</div>
</div>
<div className="tab-content absolute inset-0 w-full transition-all duration-500 opacity-0 translate-x-8 pointer-events-none" id="answerKeysTab">
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
<div className="bg-surface-container rounded-xl p-6 shadow-sm hover:shadow-md transition-all group flex flex-col h-full relative overflow-hidden">
<div className="absolute top-0 right-0 w-24 h-24 bg-tertiary-container rounded-bl-full opacity-10 -z-10 group-hover:scale-110 transition-transform"></div>
<div className="flex justify-between items-start mb-6">
<div className="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center text-tertiary">
<span className="material-symbols-outlined text-[28px]">key</span>
</div>
<div className="bg-tertiary-container/20 text-[#1A1A1A] px-3 py-1 rounded-full font-label-sm text-label-sm">Key</div>
</div>
<h3 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-2 line-clamp-2">Cellular Respiration Key</h3>
<p className="font-body-sm text-body-md text-[#1A1A1A] mb-6 flex items-center gap-2">
<span className="material-symbols-outlined text-[16px]">link</span>
                        Matches: Cellular Respiration Quiz
                    </p>
<div className="mt-auto pt-6 border-t border-surface-variant/10 flex justify-end items-center">
<button className="text-[#1A1A1A] hover:text-secondary font-title-md text-title-md flex items-center gap-2 transition-colors">
                            View Key
                            <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
</button>
</div>
</div>
<div className="bg-surface-container rounded-xl p-6 shadow-sm hover:shadow-md transition-all group flex flex-col h-full relative overflow-hidden">
<div className="absolute top-0 right-0 w-24 h-24 bg-tertiary-container rounded-bl-full opacity-10 -z-10 group-hover:scale-110 transition-transform"></div>
<div className="flex justify-between items-start mb-6">
<div className="w-12 h-12 bg-surface-container-highest rounded-lg flex items-center justify-center text-tertiary">
<span className="material-symbols-outlined text-[28px]">key</span>
</div>
<div className="bg-tertiary-container/20 text-[#1A1A1A] px-3 py-1 rounded-full font-label-sm text-label-sm">Key</div>
</div>
<h3 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-2 line-clamp-2">DNA Replication Key</h3>
<p className="font-body-sm text-body-md text-[#1A1A1A] mb-6 flex items-center gap-2">
<span className="material-symbols-outlined text-[16px]">link</span>
                        Matches: DNA Replication Lab Report
                    </p>
<div className="mt-auto pt-6 border-t border-surface-variant/10 flex justify-end items-center">
<button className="text-[#1A1A1A] hover:text-secondary font-title-md text-title-md flex items-center gap-2 transition-colors">
                            View Key
                            <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
</button>
</div>
</div>
</div>
</div>
</div>
</div>
</main></div>

    </>
  );
}
