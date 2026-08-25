/**
 * Converted from stitch_ascent_educator_dashboard/my_classes_high_contrast/my_classes_high_contrast.html
 */
export default function MyClassesHighContrast() {
  return (
    <>
<aside className="fixed left-0 top-0 h-full w-sidebar-width bg-primary z-50 flex flex-col shadow-xl overflow-y-auto border-r border-on-primary/5"><div className="px-card-padding py-10 flex items-center gap-3"><div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center rotate-45"><span className="material-symbols-outlined text-white -rotate-45">landscape</span></div><span className="font-headline-lg text-headline-lg text-white tracking-tight">ASCENT</span></div><nav className="flex-1 px-4 flex flex-col gap-1" data-active-classes="bg-surface/10 text-white font-semibold border-l-4 border-secondary"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="dashboard" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">dashboard</span>Dashboard</a><a aria-current="page" className="flex items-center px-4 py-3 rounded-lg transition-all gap-3 bg-surface/10 text-white font-semibold border-l-4 border-secondary" data-path="my-classes" href="#"><span className="material-symbols-outlined">school</span>My Classes</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="students" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">group</span>Students</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="attendance" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">how_to_reg</span>Attendance</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="lesson-plans" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">auto_stories</span>Lesson Plans</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="assignments" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">assignment</span>Assignments</a><div className="my-4 border-t border-surface-variant/10"></div><div className="px-4 py-2 text-label-sm font-label-sm text-white uppercase tracking-widest">AI Insights</div><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="misconception-heatmap" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">thermostat</span>Heatmap</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="reasoning-path-breakdown" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">route</span>Reasoning Paths</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="gap-map" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">map</span>Gap Map</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="uncertainty-flags" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">warning</span>Uncertainty</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="tracking" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">analytics</span>Tracking</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="suggested-reteach" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">psychology</span>Reteach</a><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="content-verification" href="#" style={{ color: '#FFFFFF' }}><span className="material-symbols-outlined">verified</span>Verification</a><div className="mt-auto mb-6 flex flex-col gap-1"><a className="flex items-center px-4 py-3 rounded-lg text-white hover:bg-surface/5 hover:text-white transition-all gap-3" data-path="settings" href="#"><span className="material-symbols-outlined">settings</span>Settings</a></div></nav></aside><div className="pl-sidebar-width min-h-screen bg-inverse-surface"><header className="fixed top-0 left-sidebar-width right-0 h-20 bg-inverse-surface/90 backdrop-blur-md z-40 px-margin-desktop flex items-center justify-between shadow-sm"><div className="flex-1 max-w-xl bg-surface-variant/5 rounded-full px-6 py-2 flex items-center gap-3 border border-surface-variant/10 focus-within:border-secondary transition-colors"><span className="material-symbols-outlined text-white">search</span><input className="bg-transparent border-none outline-none text-white w-full font-body-md placeholder:text-[#F5F5F5]" placeholder="Search the mountain path..." type="text"/></div><div className="flex items-center gap-6"><button className="relative text-white hover:text-white transition-colors"><span className="material-symbols-outlined">notifications</span><div className="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></div></button><div className="flex items-center gap-3 pl-6 border-l border-surface-variant/10"><div className="text-right hidden sm:block"><div className="text-body-md font-semibold text-white">Dr. Sarah Ascent</div><div className="text-label-sm text-white">Senior Educator</div></div><div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center border-2 border-secondary/50 shadow-lg"><span className="material-symbols-outlined text-secondary text-[22px]">person</span></div></div></div></header><main className="pt-20 p-margin-desktop bg-inverse-surface text-white"><div className="flex flex-col w-full relative z-0 pb-20">
{/* Hero / Title Section */}
<div className="w-full relative py-12 flex flex-col items-center justify-center bg-surface-container-low overflow-hidden rounded-b-3xl shadow-sm mb-16">
<div className="absolute inset-0 opacity-10 mix-blend-overlay pointer-events-none" data-alt="A subtle, abstract topographic map of a mountain landscape, rendered in light teal and gold lines on a dark background, representing elevation and the journey of learning. minimalist and elegant." style={{ backgroundImage: 'url(\'https://lh3.googleusercontent.com/aida-public/AB6AXuABJiPZbAH-VyGOjD_-b_GgXVDITLgeCKZhOVQDTdjyK7lT_vNIzUATBE059h1RzCruPUvk4753rYe6HZb1gBfyUwM6BWV4OksF_Wh-owFYPuuyKJhKG2swqNIFnLGcpJlHzmb0Y5GOIjyy7vxoM2QY2SHRkV0FXZcTtMbVxZuKhBVQARV9SPRR0H8AE6SCAPAU45si7yHjpTp4w2-gqy-ztzzJJ_93xa4BVss-FmJPcLpX8HMp2Mo8\')' }}></div>
<div className="absolute top-[-50%] left-[-20%] w-[150%] h-[200%] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary-fixed/20 via-transparent to-transparent opacity-40 mix-blend-color-dodge blur-3xl pointer-events-none"></div>
<div className="relative z-10 flex flex-col items-center text-center max-w-2xl px-6">
<span className="font-label-sm text-label-sm text-[#1A1A1A] tracking-widest uppercase mb-4 bg-secondary/10 px-4 py-1.5 rounded-full inline-block backdrop-blur-md">Academic Roster</span>
<h1 className="font-display-lg text-display-lg text-[#1A1A1A] mb-4">My Classes</h1>
<p className="font-body-lg text-body-lg text-[#1A1A1A]">Select a class to review progress, lesson plans, and assignments.</p>
</div>
</div>
{/* Main Content Area */}
<div className="w-full max-w-7xl mx-auto px-margin-desktop grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
{/* Class Card 1 */}
<div className="group relative bg-surface-container-lowest rounded-2xl p-card-padding flex flex-col justify-between shadow-[0_16px_40px_-15px_rgba(0,0,0,0.05)] hover:shadow-[0_24px_50px_-15px_rgba(0,0,0,0.1)] transition-all duration-300 transform hover:-translate-y-1">
<div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-secondary-fixed to-primary-fixed rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
<div>
<div className="flex justify-between items-start mb-6">
<div>
<h2 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-1">Class 10A</h2>
<span className="font-body-md text-body-md text-[#1A1A1A] uppercase tracking-wide">Mathematics</span>
</div>
<div className="w-12 h-12 rounded-full bg-primary-fixed/20 flex items-center justify-center text-[#1A1A1A] shadow-inner">
<span className="material-symbols-outlined text-2xl text-secondary">calculate</span>
</div>
</div>
<div className="space-y-4 mb-8">
<div className="flex items-center gap-3 text-[#1A1A1A] pb-3 border-b border-surface-variant/50">
<span className="material-symbols-outlined text-secondary text-xl">group</span>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Students</span>
<span className="font-title-md text-title-md text-[#1A1A1A]">32</span>
</div>
</div>
<div className="flex items-center gap-3 text-[#1A1A1A]">
<span className="material-symbols-outlined text-secondary text-xl">menu_book</span>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Current Topic</span>
<span className="font-body-lg text-body-lg text-[#1A1A1A]">Trigonometry</span>
</div>
</div>
</div>
</div>
<button className="w-full py-4 px-6 bg-secondary text-white font-title-md text-title-md rounded-xl flex items-center justify-center gap-2 hover:bg-secondary-fixed-dim hover:text-white transition-colors shadow-sm hover:shadow-md group-hover:drop-shadow-[0_0_8px_rgba(212,175,55,0.4)]">
                Enter Class
                <span className="material-symbols-outlined text-xl transition-transform group-hover:translate-x-1">arrow_forward</span>
</button>
</div>
{/* Class Card 2 */}
<div className="group relative bg-surface-container-lowest rounded-2xl p-card-padding flex flex-col justify-between shadow-[0_16px_40px_-15px_rgba(0,0,0,0.05)] hover:shadow-[0_24px_50px_-15px_rgba(0,0,0,0.1)] transition-all duration-300 transform hover:-translate-y-1">
<div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-secondary-fixed to-primary-fixed rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
<div>
<div className="flex justify-between items-start mb-6">
<div>
<h2 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-1">Class 9B</h2>
<span className="font-body-md text-body-md text-[#1A1A1A] uppercase tracking-wide">Mathematics</span>
</div>
<div className="w-12 h-12 rounded-full bg-primary-fixed/20 flex items-center justify-center text-[#1A1A1A] shadow-inner">
<span className="material-symbols-outlined text-2xl text-secondary">functions</span>
</div>
</div>
<div className="space-y-4 mb-8">
<div className="flex items-center gap-3 text-[#1A1A1A] pb-3 border-b border-surface-variant/50">
<span className="material-symbols-outlined text-secondary text-xl">group</span>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Students</span>
<span className="font-title-md text-title-md text-[#1A1A1A]">28</span>
</div>
</div>
<div className="flex items-center gap-3 text-[#1A1A1A]">
<span className="material-symbols-outlined text-secondary text-xl">menu_book</span>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Current Topic</span>
<span className="font-body-lg text-body-lg text-[#1A1A1A]">Linear Equations</span>
</div>
</div>
</div>
</div>
<button className="w-full py-4 px-6 bg-secondary text-white font-title-md text-title-md rounded-xl flex items-center justify-center gap-2 hover:bg-secondary-fixed-dim hover:text-white transition-colors shadow-sm hover:shadow-md group-hover:drop-shadow-[0_0_8px_rgba(212,175,55,0.4)]">
                Enter Class
                <span className="material-symbols-outlined text-xl transition-transform group-hover:translate-x-1">arrow_forward</span>
</button>
</div>
{/* Class Card 3 */}
<div className="group relative bg-surface-container-lowest rounded-2xl p-card-padding flex flex-col justify-between shadow-[0_16px_40px_-15px_rgba(0,0,0,0.05)] hover:shadow-[0_24px_50px_-15px_rgba(0,0,0,0.1)] transition-all duration-300 transform hover:-translate-y-1">
<div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-secondary-fixed to-primary-fixed rounded-t-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
<div>
<div className="flex justify-between items-start mb-6">
<div>
<h2 className="font-headline-lg text-headline-lg text-[#1A1A1A] mb-1">Class 11C</h2>
<span className="font-body-md text-body-md text-[#1A1A1A] uppercase tracking-wide">Mathematics</span>
</div>
<div className="w-12 h-12 rounded-full bg-primary-fixed/20 flex items-center justify-center text-[#1A1A1A] shadow-inner">
<span className="material-symbols-outlined text-2xl text-secondary">timeline</span>
</div>
</div>
<div className="space-y-4 mb-8">
<div className="flex items-center gap-3 text-[#1A1A1A] pb-3 border-b border-surface-variant/50">
<span className="material-symbols-outlined text-secondary text-xl">group</span>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Students</span>
<span className="font-title-md text-title-md text-[#1A1A1A]">25</span>
</div>
</div>
<div className="flex items-center gap-3 text-[#1A1A1A]">
<span className="material-symbols-outlined text-secondary text-xl">menu_book</span>
<div className="flex flex-col">
<span className="font-label-sm text-label-sm text-[#1A1A1A] uppercase">Current Topic</span>
<span className="font-body-lg text-body-lg text-[#1A1A1A]">Calculus Intro</span>
</div>
</div>
</div>
</div>
<button className="w-full py-4 px-6 bg-secondary text-white font-title-md text-title-md rounded-xl flex items-center justify-center gap-2 hover:bg-secondary-fixed-dim hover:text-white transition-colors shadow-sm hover:shadow-md group-hover:drop-shadow-[0_0_8px_rgba(212,175,55,0.4)]">
                Enter Class
                <span className="material-symbols-outlined text-xl transition-transform group-hover:translate-x-1">arrow_forward</span>
</button>
</div>
{/* Add New Class Card (Ghost) */}
<div className="group relative border-2 border-dashed border-surface-variant/30 rounded-2xl p-card-padding flex flex-col items-center justify-center text-center hover:bg-surface-container-low transition-colors duration-300 cursor-pointer min-h-[320px]">
<div className="w-16 h-16 rounded-full bg-surface-variant/10 flex items-center justify-center text-white group-hover:scale-110 group-hover:bg-primary/5 group-hover:text-primary transition-all duration-300 mb-4">
<span className="material-symbols-outlined text-3xl">add</span>
</div>
<h3 className="font-title-md text-title-md text-white transition-colors">Create New Class</h3>
<p className="font-body-md text-body-md text-white mt-2">Add a new section to your roster</p>
</div>
</div>
</div></main></div>

    </>
  );
}
