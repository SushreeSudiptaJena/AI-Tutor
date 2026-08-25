/**
 * Converted from stitch_ascent_educator_dashboard/attendance_tracker_high_contrast/attendance_tracker_high_contrast.html
 */
export default function AttendanceTrackerHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-[#1A1A1A] -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-[#FFFFFF] tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-secondary-container font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">dashboard</span>Dashboard</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">menu_book</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">group</span>Students</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-[#FFFFFF] font-semibold border-l-4 border-secondary" data-path="attendance" href="#"><span className="material-symbols-outlined text-secondary-container">calendar_month</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">book</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">assignment</span>Assignments</a><div className="my-4 border-t border-[#FFFFFF]/20"></div><div className="px-4 py-2 text-label-sm font-label-sm text-[#FFFFFF] uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">account_tree</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">bar_chart</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">school</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/10 transition-all gap-3" href="#"><span className="material-symbols-outlined text-secondary-container">verified_user</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-[#FFFFFF] hover:bg-surface/5 transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined text-[#FFFFFF]">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-[#FFFFFF]">search</span><input className="bg-transparent border-none outline-none text-[#FFFFFF] w-full font-body-md" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-[#FFFFFF] hover:text-secondary-container transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-[#FFFFFF]/20"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-[#FFFFFF]">Dr. Sarah Ascent</div><div className="text-label-sm text-[#FFFFFF]">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-[#FFFFFF]"><div className="flex flex-col w-full gap-10">
<div className="flex flex-col lg:flex-row gap-6 lg:items-end justify-between">
<div>
<h1 className="font-display-lg text-display-lg text-[#FFFFFF] mb-2">Attendance</h1>
<p className="font-body-lg text-body-lg text-[#FFFFFF]">Track presence, patterns, and participation.</p>
</div>
<div className="flex items-center gap-4">
<div className="relative min-w-[200px]">
<select className="w-full appearance-none bg-surface-container hover:bg-surface-container-high transition-colors text-[#1A1A1A] font-title-md text-title-md py-3 pl-4 pr-10 rounded-xl focus:outline-none focus:ring-2 focus:ring-secondary cursor-pointer border-none shadow-sm">
<option>AP Physics - Block A</option>
<option>Physics 101 - Block B</option>
<option>Astrophysics - Block C</option>
</select>
<span className="material-symbols-outlined absolute right-4 top-1/2 -translate-y-1/2 text-[#1A1A1A] pointer-events-none">expand_more</span>
</div>
<button className="bg-secondary hover:bg-secondary-fixed transition-colors text-[#1A1A1A] font-title-md text-title-md py-3 px-6 rounded-xl flex items-center gap-2 shadow-md hover:shadow-lg transform hover:-translate-y-0.5">
<span className="material-symbols-outlined font-variation-settings-'FILL'-1">edit_calendar</span>
                Mark Today
            </button>
</div>
</div>
<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
<div className="bg-surface-container-low p-6 rounded-2xl shadow-sm flex items-center gap-4 relative overflow-hidden group">
<div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0 relative z-10 group-hover:scale-110 transition-transform">
<span className="material-symbols-outlined text-primary text-[28px] font-variation-settings-'FILL'-1">check_circle</span>
</div>
<div className="relative z-10">
<p className="font-label-sm text-label-sm text-[#1A1A1A] uppercase tracking-wider mb-1">Present Today</p>
<p className="font-headline-lg text-headline-lg text-[#1A1A1A]">24 <span className="font-body-md text-body-md text-[#1A1A1A] font-normal">/ 28</span></p>
</div>
<div className="absolute -bottom-6 -right-6 w-32 h-32 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-colors"></div>
</div>
<div className="bg-surface-container-low p-6 rounded-2xl shadow-sm flex items-center gap-4 relative overflow-hidden group">
<div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center shrink-0 relative z-10 group-hover:scale-110 transition-transform">
<span className="material-symbols-outlined text-error text-[28px]">cancel</span>
</div>
<div className="relative z-10">
<p className="font-label-sm text-label-sm text-[#1A1A1A] uppercase tracking-wider mb-1">Absent Today</p>
<p className="font-headline-lg text-headline-lg text-[#1A1A1A]">3</p>
</div>
<div className="absolute -bottom-6 -right-6 w-32 h-32 bg-error/5 rounded-full blur-2xl group-hover:bg-error/10 transition-colors"></div>
</div>
<div className="bg-surface-container-low p-6 rounded-2xl shadow-sm flex items-center gap-4 relative overflow-hidden group">
<div className="w-12 h-12 rounded-full bg-secondary-container/30 flex items-center justify-center shrink-0 relative z-10 group-hover:scale-110 transition-transform">
<span className="material-symbols-outlined text-secondary-container text-[28px]">schedule</span>
</div>
<div className="relative z-10">
<p className="font-label-sm text-label-sm text-[#1A1A1A] uppercase tracking-wider mb-1">Late Today</p>
<p className="font-headline-lg text-headline-lg text-[#1A1A1A]">1</p>
</div>
<div className="absolute -bottom-6 -right-6 w-32 h-32 bg-secondary/5 rounded-full blur-2xl group-hover:bg-secondary/10 transition-colors"></div>
</div>
</div>
<div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
<div className="xl:col-span-2 bg-surface-container-lowest rounded-3xl shadow-md overflow-hidden flex flex-col">
<div className="bg-primary p-6 flex items-center justify-between">
<h2 className="font-title-md text-title-md text-[#FFFFFF]">Weekly Overview</h2>
<div className="flex items-center gap-2 text-[#FFFFFF] font-label-sm text-label-sm">
<button className="hover:text-[#FFFFFF] transition-colors"><span className="material-symbols-outlined text-[20px]">chevron_left</span></button>
<span className="">Oct 16 - 20</span>
<button className="hover:text-[#FFFFFF] transition-colors"><span className="material-symbols-outlined text-[20px]">chevron_right</span></button>
</div>
</div>
<div className="overflow-x-auto">
<table className="w-full text-left border-collapse">
<thead>
<tr className="bg-surface-container-low font-label-sm text-label-sm uppercase tracking-wider text-[#1A1A1A]">
<th className="p-4 pl-6 font-medium whitespace-nowrap">Student</th>
<th className="p-4 font-medium text-center w-16">M <span className="block text-[10px]">16</span></th>
<th className="p-4 font-medium text-center w-16">T <span className="block text-[10px]">17</span></th>
<th className="p-4 font-medium text-center w-16">W <span className="block text-[10px]">18</span></th>
<th className="p-4 font-medium text-center w-16">T <span className="block text-[10px]">19</span></th>
<th className="p-4 font-medium text-center w-16 bg-primary/5">F <span className="block text-[10px]">20</span></th>
</tr>
</thead>
<tbody className="font-body-md text-body-md text-[#1A1A1A] divide-y divide-[#1A1A1A]/10">
<tr className="hover:bg-surface-container transition-colors group">
<td className="p-4 pl-6 flex items-center gap-3">
<div className="w-8 h-8 rounded-full bg-tertiary-fixed flex items-center justify-center font-title-md text-[14px] text-[#1A1A1A]">EA</div>
<span className="font-medium">Elena Alvarez</span>
</td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center bg-primary/5 relative group-hover:bg-transparent">
<button className="w-6 h-6 rounded flex items-center justify-center hover:bg-surface-variant/50 transition-colors mx-auto group/btn">
<span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1 group-hover/btn:scale-110 transition-transform">check_circle</span>
</button>
</td>
</tr>
<tr className="hover:bg-surface-container transition-colors group">
<td className="p-4 pl-6 flex items-center gap-3">
<div className="w-8 h-8 rounded-full bg-surface-variant flex items-center justify-center font-title-md text-[14px] text-[#1A1A1A]">MC</div>
<span className="">Marcus Chen</span>
</td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-secondary text-[20px] font-variation-settings-'FILL'-1">schedule</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center bg-primary/5 relative group-hover:bg-transparent">
<button className="w-6 h-6 rounded flex items-center justify-center hover:bg-surface-variant/50 transition-colors mx-auto group/btn">
<span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1 group-hover/btn:scale-110 transition-transform">check_circle</span>
</button>
</td>
</tr>
<tr className="hover:bg-surface-container transition-colors group">
<td className="p-4 pl-6 flex items-center gap-3">
<div className="w-8 h-8 rounded-full bg-error-container flex items-center justify-center font-title-md text-[14px] text-[#1A1A1A]">SD</div>
<span className="">Sarah Davis</span>
</td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-error text-[20px]">cancel</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-error text-[20px]">cancel</span></td>
<td className="p-4 text-center bg-primary/5 relative group-hover:bg-transparent">
<button className="w-6 h-6 rounded flex items-center justify-center hover:bg-surface-variant/50 transition-colors mx-auto group/btn">
<span className="material-symbols-outlined text-error text-[20px] group-hover/btn:scale-110 transition-transform">cancel</span>
</button>
</td>
</tr>
<tr className="hover:bg-surface-container transition-colors group">
<td className="p-4 pl-6 flex items-center gap-3">
<div className="w-8 h-8 rounded-full bg-tertiary flex items-center justify-center font-title-md text-[14px] text-[#FFFFFF]">JL</div>
<span className="">James Lee</span>
</td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center bg-primary/5 relative group-hover:bg-transparent">
<button className="w-6 h-6 rounded flex items-center justify-center hover:bg-surface-variant/50 transition-colors mx-auto group/btn">
<span className="material-symbols-outlined text-secondary text-[20px] font-variation-settings-'FILL'-1 group-hover/btn:scale-110 transition-transform">schedule</span>
</button>
</td>
</tr>
<tr className="hover:bg-surface-container transition-colors group">
<td className="p-4 pl-6 flex items-center gap-3">
<div className="w-8 h-8 rounded-full bg-surface-variant flex items-center justify-center font-title-md text-[14px] text-[#1A1A1A]">OW</div>
<span className="">Olivia Wilson</span>
</td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-error text-[20px]">cancel</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center"><span className="material-symbols-outlined text-primary text-[20px] font-variation-settings-'FILL'-1">check_circle</span></td>
<td className="p-4 text-center bg-primary/5 relative group-hover:bg-transparent">
<button className="w-6 h-6 rounded flex items-center justify-center hover:bg-surface-variant/50 transition-colors mx-auto group/btn">
<span className="material-symbols-outlined text-primary/30 text-[20px] group-hover/btn:text-primary transition-colors">radio_button_unchecked</span>
</button>
</td>
</tr>
</tbody>
</table>
</div>
<div className="mt-auto bg-surface-container-low p-4 flex justify-between items-center border-t border-[#1A1A1A]/10">
<span className="font-label-sm text-label-sm text-[#1A1A1A]">Showing 5 of 28 students</span>
<div className="flex gap-2">
<button className="w-8 h-8 rounded-lg flex items-center justify-center text-[#1A1A1A] hover:bg-surface-variant/20 transition-colors opacity-50 cursor-not-allowed"><span className="material-symbols-outlined text-[18px]">chevron_left</span></button>
<button className="w-8 h-8 rounded-lg flex items-center justify-center bg-primary text-[#FFFFFF] shadow-sm font-label-sm text-label-sm">1</button>
<button className="w-8 h-8 rounded-lg flex items-center justify-center text-[#1A1A1A] hover:bg-surface-variant/20 transition-colors font-label-sm text-label-sm">2</button>
<button className="w-8 h-8 rounded-lg flex items-center justify-center text-[#1A1A1A] hover:bg-surface-variant/20 transition-colors font-label-sm text-label-sm">3</button>
<button className="w-8 h-8 rounded-lg flex items-center justify-center text-[#1A1A1A] hover:bg-surface-variant/20 transition-colors"><span className="material-symbols-outlined text-[18px]">chevron_right</span></button>
</div>
</div>
</div>
<div className="flex flex-col gap-8">
<div className="bg-surface-container-lowest p-6 rounded-3xl shadow-md">
<h2 className="font-title-md text-title-md text-[#1A1A1A] mb-6">Monthly Summary</h2>
<div className="flex flex-col gap-4">
<div className="flex items-end gap-2 h-40">
<div className="flex-1 flex flex-col justify-end group">
<div className="w-full bg-primary/20 rounded-t-sm group-hover:bg-primary/30 transition-colors h-[15%]" title="Absent"></div>
<div className="w-full bg-secondary/80 rounded-t-sm group-hover:bg-secondary transition-colors h-[5%]" title="Late"></div>
<div className="w-full bg-primary rounded-t-sm group-hover:bg-primary/90 transition-colors h-[80%]" title="Present"></div>
</div>
<div className="flex-1 flex flex-col justify-end group">
<div className="w-full bg-primary/20 rounded-t-sm group-hover:bg-primary/30 transition-colors h-[10%]" title="Absent"></div>
<div className="w-full bg-secondary/80 rounded-t-sm group-hover:bg-secondary transition-colors h-[12%]" title="Late"></div>
<div className="w-full bg-primary rounded-t-sm group-hover:bg-primary/90 transition-colors h-[78%]" title="Present"></div>
</div>
<div className="flex-1 flex flex-col justify-end group">
<div className="w-full bg-primary/20 rounded-t-sm group-hover:bg-primary/30 transition-colors h-[5%]" title="Absent"></div>
<div className="w-full bg-secondary/80 rounded-t-sm group-hover:bg-secondary transition-colors h-[5%]" title="Late"></div>
<div className="w-full bg-primary rounded-t-sm group-hover:bg-primary/90 transition-colors h-[90%]" title="Present"></div>
</div>
<div className="flex-1 flex flex-col justify-end group">
<div className="w-full bg-primary/20 rounded-t-sm group-hover:bg-primary/30 transition-colors h-[25%]" title="Absent"></div>
<div className="w-full bg-secondary/80 rounded-t-sm group-hover:bg-secondary transition-colors h-[2%]" title="Late"></div>
<div className="w-full bg-primary rounded-t-sm group-hover:bg-primary/90 transition-colors h-[73%]" title="Present"></div>
</div>
<div className="flex-1 flex flex-col justify-end group">
<div className="w-full bg-primary/20 rounded-t-sm group-hover:bg-primary/30 transition-colors h-[8%]" title="Absent"></div>
<div className="w-full bg-secondary/80 rounded-t-sm group-hover:bg-secondary transition-colors h-[15%]" title="Late"></div>
<div className="w-full bg-primary rounded-t-sm group-hover:bg-primary/90 transition-colors h-[77%]" title="Present"></div>
</div>
</div>
<div className="flex justify-between font-label-sm text-label-sm text-[#1A1A1A]">
<span className="">W1</span>
<span className="">W2</span>
<span className="">W3</span>
<span className="">W4</span>
<span className="">W5</span>
</div>
</div>
<div className="mt-6 flex flex-wrap gap-4 font-label-sm text-label-sm text-[#1A1A1A] font-medium">
<div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-primary"></div> Present (85%)</div>
<div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-secondary"></div> Late (5%)</div>
<div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-primary/20"></div> Absent (10%)</div>
</div>
</div>
<div className="bg-tertiary p-6 rounded-3xl shadow-md text-[#FFFFFF] relative overflow-hidden">
<div className="absolute -right-10 -top-10 w-40 h-40 bg-tertiary-fixed-dim/20 rounded-full blur-3xl"></div>
<h3 className="font-title-md text-title-md mb-2 relative z-10">Attendance Alert</h3>
<p className="font-body-md text-body-md text-[#FFFFFF] mb-4 relative z-10">Sarah Davis has missed 3 consecutive classes. Review required.</p>
<button className="bg-tertiary-fixed text-[#1A1A1A] hover:bg-tertiary-fixed-dim transition-colors font-label-sm text-label-sm uppercase tracking-wider py-2 px-4 rounded-lg relative z-10 flex items-center gap-2">
                    Review Details <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
</button>
</div>
</div>
</div>
</div></main></div>

    </>
  );
}
