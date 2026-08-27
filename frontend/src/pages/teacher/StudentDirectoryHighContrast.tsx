/**
 * Converted from stitch_ascent_educator_dashboard/student_directory_high_contrast/student_directory_high_contrast.html
 */
export default function StudentDirectoryHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-on-secondary -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="dashboard" href="#"><span className="material-symbols-outlined text-secondary">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="my-classes" href="#"><span className="material-symbols-outlined text-secondary">school</span>My Classes</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="students" href="#"><span className="material-symbols-outlined text-secondary">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="attendance" href="#"><span className="material-symbols-outlined text-secondary">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="lesson-plans" href="#"><span className="material-symbols-outlined text-secondary">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="assignments" href="#"><span className="material-symbols-outlined text-secondary">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="misconception-heatmap" href="#"><span className="material-symbols-outlined text-secondary">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="reasoning-path-breakdown" href="#"><span className="material-symbols-outlined text-secondary">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="gap-map" href="#"><span className="material-symbols-outlined text-secondary">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="uncertainty-flags" href="#"><span className="material-symbols-outlined text-secondary">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="tracking" href="#"><span className="material-symbols-outlined text-secondary">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="suggested-reteach" href="#"><span className="material-symbols-outlined text-secondary">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg hover:bg-surface/5 hover:text-white transition-all gap-3 text-white" data-path="content-verification" href="#"><span className="material-symbols-outlined text-secondary">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined text-secondary">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-[36rem] bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-white">search</span><input className="bg-transparent border-none outline-none text-white w-full font-body-md placeholder-white" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-white hover:text-secondary-container transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-white">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full relative">
<div className="absolute top-0 right-0 w-96 h-96 bg-primary-fixed/20 rounded-full blur-3xl -z-10 mix-blend-multiply opacity-50 transform translate-x-1/2 -translate-y-1/4"></div>
<header className="flex items-end justify-between w-full mb-10 z-10">
<div className="flex flex-col gap-2">
<div className="flex items-center gap-3">
<span className="material-symbols-outlined text-secondary text-2xl">groups</span>
<h1 className="font-display-lg text-display-lg text-white m-0 p-0 tracking-tight">Student Roster</h1>
</div>
<p className="font-body-lg text-body-lg text-white max-w-2xl">Monitor progress, identify conceptual gaps, and review individual mastery paths across all active cohorts.</p>
</div>
<div className="flex items-center gap-4 hidden md:flex">
<div className="px-4 py-2 bg-surface-container rounded-full flex items-center gap-2 shadow-sm cursor-pointer hover:bg-surface-container-high transition-colors">
<div className="w-2 h-2 rounded-full bg-error animate-pulse"></div>
<span className="font-label-sm text-label-sm text-ink">3 Alerts Active</span>
</div>
<button className="px-6 py-3 bg-secondary text-white rounded-lg font-title-md text-title-md shadow-md hover:bg-secondary-container hover:text-white transition-all flex items-center gap-2">
<span className="material-symbols-outlined">add</span> New Student
      </button>
</div>
</header>
<section className="flex flex-col lg:flex-row gap-6 mb-8 w-full z-10">
<div className="flex-1 bg-surface-container-lowest rounded-xl p-card-padding shadow-md flex items-center gap-6">
<div className="w-14 h-14 rounded-full bg-primary flex items-center justify-center text-white shadow-sm shrink-0">
<span className="material-symbols-outlined text-3xl text-secondary">monitoring</span>
</div>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-ink uppercase tracking-wider mb-1">Cohort Mastery Average</span>
<div className="flex items-baseline gap-2">
<span className="font-display-lg text-display-lg text-ink leading-none">78%</span>
<span className="font-body-md text-body-md text-ink font-semibold flex items-center"><span className="material-symbols-outlined text-sm">trending_up</span> +4.2%</span>
</div>
</div>
</div>
<div className="flex-1 bg-surface-container-lowest rounded-xl p-card-padding shadow-md flex items-center gap-6 relative overflow-hidden">
<div className="absolute right-0 bottom-0 w-32 h-32 bg-secondary/10 rounded-tl-full"></div>
<div className="flex flex-col flex-1 z-10">
<span className="font-label-sm text-label-sm text-ink uppercase tracking-wider mb-1">Attention Required</span>
<span className="font-headline-lg text-headline-lg text-ink mb-2">12 Students</span>
<div className="w-full h-1 bg-surface-variant rounded-full overflow-hidden">
<div className="h-full bg-error w-1/4 rounded-full"></div>
</div>
</div>
</div>
</section>
<section className="w-full bg-surface-container-lowest rounded-xl shadow-lg relative z-10 flex flex-col overflow-hidden">
<div className="p-6 border-b-2 border-surface-container flex flex-col md:flex-row items-center justify-between gap-4 bg-surface-container-lowest">
<div className="relative w-full md:w-96 flex items-center">
<span className="material-symbols-outlined absolute left-4 text-ink z-10">search</span>
<input className="w-full pl-12 pr-4 py-3 bg-surface rounded-lg border-2 border-transparent focus:border-secondary focus:bg-surface-container-lowest outline-none transition-all font-body-md text-ink shadow-inner text-body-md placeholder:text-ink" id="studentSearch" placeholder="Search by name, ID, or tag..." type="text"/>
</div>
<div className="flex items-center gap-3 w-full md:w-auto overflow-x-auto pb-2 md:pb-0 hide-scrollbar">
<button className="px-4 py-2 rounded-full border-2 border-outline-variant text-ink font-label-sm text-label-sm hover:border-secondary hover:text-ink transition-colors whitespace-nowrap flex items-center gap-1">
<span className="material-symbols-outlined text-sm">filter_list</span> All Statuses
        </button>
<button className="px-4 py-2 rounded-full border-2 border-outline-variant text-ink font-label-sm text-label-sm hover:border-secondary hover:text-ink transition-colors whitespace-nowrap">Mastered (80%+)</button>
<button className="px-4 py-2 rounded-full border-2 border-error/50 text-on-primary font-label-sm text-label-sm bg-error-container/20 hover:bg-error-container/40 transition-colors whitespace-nowrap">Flagged</button>
<button className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-ink hover:bg-surface-variant transition-colors ml-2 shrink-0">
<span className="material-symbols-outlined">more_vert</span>
</button>
</div>
</div>
<div className="overflow-x-auto w-full">
<table className="w-full text-left border-collapse min-w-[800px]">
<thead>
<tr className="bg-surface-container-lowest border-b-2 border-surface-container text-label-sm font-label-sm uppercase tracking-wider text-ink">
<th className="py-4 px-6 font-medium cursor-pointer hover:text-ink transition-colors w-1/3">Student Name <span className="material-symbols-outlined text-[14px] align-middle">arrow_drop_down</span></th>
<th className="py-4 px-6 font-medium cursor-pointer hover:text-ink transition-colors w-1/4">Mastery %</th>
<th className="py-4 px-6 font-medium cursor-pointer hover:text-ink transition-colors w-1/4">Last Activity</th>
<th className="py-4 px-6 font-medium text-right w-1/6">Status</th>
</tr>
</thead>
<tbody className="font-body-md text-body-md text-ink" id="studentTableBody">
<tr className="border-b border-surface-variant/50 hover:bg-surface/50 transition-colors group cursor-pointer">
<td className="py-4 px-6">
<div className="flex items-center gap-4">
<div className="w-10 h-10 rounded-full bg-primary-fixed text-on-primary flex items-center justify-center font-title-md text-title-md shrink-0">EL</div>
<div className="flex flex-col">
<span className="font-title-md text-title-md text-ink group-hover:text-ink transition-colors">Elena Rodriguez</span>
<span className="font-label-sm text-label-sm text-ink">ID: 847291</span>
</div>
</div>
</td>
<td className="py-4 px-6">
<div className="flex items-center gap-3">
<span className="font-headline-lg-mobile text-headline-lg-mobile w-12 text-right">92%</span>
<div className="w-24 h-2 bg-surface-container rounded-full overflow-hidden">
<div className="h-full bg-primary w-[92%] rounded-full shadow-[0_0_8px_rgba(0,52,43,0.5)]"></div>
</div>
</div>
</td>
<td className="py-4 px-6 text-ink">2 hours ago<br/><span className="text-label-sm font-label-sm text-ink">Algebra II: Quadratics</span></td>
<td className="py-4 px-6 text-right">
<span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-fixed/20 text-on-primary rounded-full font-label-sm text-label-sm font-semibold">
<div className="w-1.5 h-1.5 rounded-full bg-primary-container"></div> On Track
              </span>
</td>
</tr>
<tr className="border-b border-surface-variant/50 hover:bg-surface/50 transition-colors group cursor-pointer bg-error-container/5">
<td className="py-4 px-6">
<div className="flex items-center gap-4">
<div className="w-10 h-10 rounded-full bg-surface-variant text-ink flex items-center justify-center font-title-md text-title-md shrink-0">JC</div>
<div className="flex flex-col">
<span className="font-title-md text-title-md text-ink group-hover:text-ink transition-colors">Julian Chen</span>
<span className="font-label-sm text-label-sm text-ink">ID: 847302</span>
</div>
</div>
</td>
<td className="py-4 px-6">
<div className="flex items-center gap-3">
<span className="font-headline-lg-mobile text-headline-lg-mobile w-12 text-right">45%</span>
<div className="w-24 h-2 bg-surface-container rounded-full overflow-hidden">
<div className="h-full bg-error w-[45%] rounded-full"></div>
</div>
</div>
</td>
<td className="py-4 px-6 text-ink">Yesterday<br/><span className="text-label-sm font-label-sm text-ink">Calculus: Limits</span></td>
<td className="py-4 px-6 text-right">
<span className="inline-flex items-center gap-1 px-3 py-1 bg-error-container text-on-primary rounded-full font-label-sm text-label-sm border border-error/20 font-semibold">
<span className="material-symbols-outlined text-[14px]">warning</span> Intervention
              </span>
</td>
</tr>
<tr className="border-b border-surface-variant/50 hover:bg-surface/50 transition-colors group cursor-pointer">
<td className="py-4 px-6">
<div className="flex items-center gap-4">
<div className="w-10 h-10 rounded-full bg-tertiary-fixed text-ink flex items-center justify-center font-title-md text-title-md shrink-0">MK</div>
<div className="flex flex-col">
<span className="font-title-md text-title-md text-ink group-hover:text-ink transition-colors">Maya Kapoor</span>
<span className="font-label-sm text-label-sm text-ink">ID: 847115</span>
</div>
</div>
</td>
<td className="py-4 px-6">
<div className="flex items-center gap-3">
<span className="font-headline-lg-mobile text-headline-lg-mobile w-12 text-right">76%</span>
<div className="w-24 h-2 bg-surface-container rounded-full overflow-hidden">
<div className="h-full bg-secondary w-[76%] rounded-full"></div>
</div>
</div>
</td>
<td className="py-4 px-6 text-ink">Today, 9:15 AM<br/><span className="text-label-sm font-label-sm text-ink">Geometry: Proofs</span></td>
<td className="py-4 px-6 text-right">
<span className="inline-flex items-center gap-1 px-3 py-1 bg-surface-container text-ink rounded-full font-label-sm text-label-sm font-semibold">
<div className="w-1.5 h-1.5 rounded-full bg-outline"></div> Monitoring
              </span>
</td>
</tr>
<tr className="border-b border-surface-variant/50 hover:bg-surface/50 transition-colors group cursor-pointer">
<td className="py-4 px-6">
<div className="flex items-center gap-4">
<div className="w-10 h-10 rounded-full bg-surface-variant text-ink flex items-center justify-center font-title-md text-title-md shrink-0 bg-cover bg-center" data-alt="Close up portrait photograph of a young male student looking confident, well-lit studio lighting, cinematic, soft background blur, professional headshot style. Colors should complement deep teals and creams." style={{ backgroundImage: 'url(\'https://lh3.googleusercontent.com/aida-public/AB6AXuC45OTkDRbOixUNU_dWpiIF-s5yYG553AlAQ2cWtpv_yhdVbdnk5gwTtu6z1PAsfRhCRh0gVXbTUNuyuPzL5Vn1WO08lPaLvUcPXVnEYpTHJIgpuDKyJWhIjWiexQZlI--ZNuSRCzlokxdWQGHNX0pfJdZYL6-1k3sZIsmco5Q6aXhWD68elrdFXtXpK6RZjQMFWxl7xyo2c5U8qCa0qGUNKoDXU066GM8K_7bFhYWsl5A0kreM1bFi\')' }}></div>
<div className="flex flex-col">
<span className="font-title-md text-title-md text-ink group-hover:text-ink transition-colors">David Smith</span>
<span className="font-label-sm text-label-sm text-ink">ID: 847422</span>
</div>
</div>
</td>
<td className="py-4 px-6">
<div className="flex items-center gap-3">
<span className="font-headline-lg-mobile text-headline-lg-mobile w-12 text-right">88%</span>
<div className="w-24 h-2 bg-surface-container rounded-full overflow-hidden">
<div className="h-full bg-primary w-[88%] rounded-full"></div>
</div>
</div>
</td>
<td className="py-4 px-6 text-ink">3 days ago<br/><span className="text-label-sm font-label-sm text-ink">Stats: Probability</span></td>
<td className="py-4 px-6 text-right">
<span className="inline-flex items-center gap-1 px-3 py-1 bg-primary-fixed/20 text-on-primary rounded-full font-label-sm text-label-sm font-semibold">
<div className="w-1.5 h-1.5 rounded-full bg-primary-container"></div> On Track
              </span>
</td>
</tr>
</tbody>
</table>
</div>
<div className="p-4 border-t-2 border-surface-container bg-surface-container-lowest flex items-center justify-between">
<span className="text-label-sm font-label-sm text-ink">Showing 1-4 of 142 students</span>
<div className="flex items-center gap-2">
<button className="w-8 h-8 rounded-full flex items-center justify-center text-ink hover:bg-surface-container transition-colors disabled:opacity-50"><span className="material-symbols-outlined text-sm">chevron_left</span></button>
<button className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center font-label-sm text-label-sm shadow-md">1</button>
<button className="w-8 h-8 rounded-full flex items-center justify-center text-ink hover:bg-surface-container transition-colors font-label-sm text-label-sm">2</button>
<button className="w-8 h-8 rounded-full flex items-center justify-center text-ink hover:bg-surface-container transition-colors font-label-sm text-label-sm">3</button>
<span className="text-ink mx-1">...</span>
<button className="w-8 h-8 rounded-full flex items-center justify-center text-ink hover:bg-surface-container transition-colors"><span className="material-symbols-outlined text-sm">chevron_right</span></button>
</div>
</div>
</section>
</div>
</main></div>

    </>
  );
}
