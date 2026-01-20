import { useNavigate, Link } from 'react-router-dom'
import { FaFileUpload, FaBalanceScale, FaArrowRight, FaHistory, FaGavel, FaExternalLinkAlt, FaLandmark, FaBriefcase, FaHome, FaChartLine } from 'react-icons/fa'

const landmarkCases = [
    {
        year: "2015",
        cases: [
            {
                title: "Shreya Singhal v. Union of India",
                desc: "Struck down Section 66A of the IT Act. Major victory for free speech online.",
                query: "Explain Shreya Singhal v. Union of India and Section 66A"
            }
        ]
    },
    {
        year: "2016",
        cases: [
            {
                title: "NALSA v. Union of India",
                desc: "Recognized transgender persons as a third gender.",
                query: "What was the NALSA v Union of India verdict about transgender rights?"
            }
        ]
    },
    {
        year: "2017",
        cases: [
            {
                title: "K. S. Puttaswamy v. Union of India",
                desc: "Declared Right to Privacy a Fundamental Right.",
                query: "Explain the K. S. Puttaswamy v. Union of India Right to Privacy judgment"
            }
        ]
    },
    {
        year: "2018",
        cases: [
            {
                title: "Navtej Singh Johar v. Union of India",
                desc: "Decriminalized homosexuality (Section 377).",
                query: "What did the Supreme Court say in Navtej Singh Johar v. Union of India?"
            },
            {
                title: "Indian Young Lawyers Assn v. Kerala",
                desc: "Allowed women entry into Sabarimala temple.",
                query: "Explain the Sabarimala verdict Indian Young Lawyers Association"
            }
        ]
    },
    {
        year: "2019",
        cases: [
            {
                title: "M. Siddiq v. Mahant Suresh Das",
                desc: "Ayodhya / Ram Mandir verdict.",
                query: "Summary of M. Siddiq v. Mahant Suresh Das Ayodhya verdict"
            }
        ]
    },
    {
        year: "2020",
        cases: [
            {
                title: "Anuradha Bhasin v. Union of India",
                desc: "Ruled on Internet shutdowns in J&K.",
                query: "What was the ruling in Anuradha Bhasin v. Union of India regarding internet shutdowns?"
            },
            {
                title: "Arnab Goswami v. Maharashtra",
                desc: "Bail & personal liberty principles.",
                query: "Explain Arnab Goswami v. State of Maharashtra bail principles"
            }
        ]
    },
    {
        year: "2021",
        cases: [
            {
                title: "In Re: Distribution of Essential Supplies",
                desc: "SC intervention during COVID oxygen crisis.",
                query: "What was the Supreme Court's role in In Re Distribution of Essential Supplies?"
            }
        ]
    },
    {
        year: "2022",
        cases: [
            {
                title: "Vijay Madanlal Choudhary v. UOI",
                desc: "Upheld stringent PMLA provisions.",
                query: "Explain Vijay Madanlal Choudhary v. Union of India PMLA judgment"
            },
            {
                title: "X v. Principal Secretary, Health",
                desc: "Expanded abortion rights to unmarried women.",
                query: "What is the X v. Principal Secretary Health judgment on abortion rights?"
            }
        ]
    },
    {
        year: "2023",
        cases: [
            {
                title: "Supriyo v. Union of India",
                desc: "Same-sex marriage petitions verdict.",
                query: "Summary of Supriyo v. Union of India same sex marriage verdict"
            },
            {
                title: "Subhash Desai v. Principal Secretary",
                desc: "Maharashtra political crisis judgment.",
                query: "What happened in Subhash Desai v. Principal Secretary Maharashtra political crisis?"
            }
        ]
    },
    {
        year: "2024",
        cases: [
            {
                title: "Electoral Bonds Case",
                desc: "Electoral Bonds declared unconstitutional.",
                query: "Explain the Supreme Court verdict on Electoral Bonds 2024"
            }
        ]
    },
    {
        year: "2025",
        cases: [
            {
                title: "Article 370 Review / UCC",
                desc: "Ongoing debates on 370 Review & Uniform Civil Code.",
                query: "What is the status of Article 370 review petitions and Uniform Civil Code?"
            }
        ]
    }
];

const topGenres = [
    {
        rank: "1",
        title: "Constitutional Law",
        volume: "30-35%",
        icon: <FaLandmark />,
        desc: "Federalism, fundamental rights, separation of powers.",
        issues: ["Fundamental Rights", "Amendments", "Judicial Review"],
        trend: "Highest search interest + highest citation rate",
        color: "from-amber-500 to-orange-600"
    },
    {
        rank: "2",
        title: "Criminal Law & Procedure",
        volume: "20-25%",
        icon: <FaGavel />,
        desc: "Appeals, bail, personal liberty & sentencing.",
        issues: ["Bail Jurisprudence", "UAPA / PMLA", "Custodial Violence"],
        trend: "Shift towards liberty-centric interpretation",
        color: "from-red-500 to-rose-600"
    },
    {
        rank: "3",
        title: "Service & Employment Law",
        volume: "15-18%",
        icon: <FaBriefcase />,
        desc: "Govt employees, promotions, pension disputes.",
        issues: ["Promotions", "Pension", "Disciplinary Action"],
        trend: "Lowest media coverage, high volume",
        color: "from-blue-500 to-cyan-600"
    },
    {
        rank: "4",
        title: "Civil & Property Law",
        volume: "12-15%",
        icon: <FaHome />,
        desc: "Land acquisition, inheritance, contract enforcement.",
        issues: ["Title Disputes", "Inheritance", "Arbitration"],
        trend: "Cases often span decades",
        color: "from-emerald-500 to-teal-600"
    },
    {
        rank: "5",
        title: "Admin & Regulatory Law",
        volume: "8-12%",
        icon: <FaChartLine />,
        desc: "SEBI / RBI / Telecom / Environmental challenges.",
        issues: ["Tender Disputes", "Policy Challenges", "Eco Clearances"],
        trend: "Fast growing since 2016",
        color: "from-purple-500 to-violet-600"
    }
];

export default function Home() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-neutral-950 text-white font-sans selection:bg-white selection:text-black overflow-hidden relative">

            {/* Subtle Gradient Spots (Monochrome) */}
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-white/5 rounded-full blur-[120px] pointer-events-none"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-white/5 rounded-full blur-[150px] pointer-events-none"></div>

            <div className="container mx-auto px-6 py-20 flex flex-col items-center justify-start relative z-10">

                {/* Header / Hero */}
                <div className="text-center mb-12 space-y-6">
                    <h1 className="text-5xl md:text-7xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40 drop-shadow-sm p-3">
                        Is This Legal?
                    </h1>
                    <p className="text-lg md:text-xl text-neutral-400 font-light max-w-2xl mx-auto leading-relaxed">
                        Your personal AI legal expert. Simplify complex regulations, analyze documents, and get answers in seconds.
                    </p>
                </div>

                {/* Action Cards Container */}
                <div className="flex flex-wrap justify-center gap-6 w-full mb-20">

                    {/* CTA 1: Upload & Summary */}
                    <button
                        onClick={() => navigate('/upload')}
                        className="group relative overflow-hidden rounded-2xl glass-card p-6 hover:bg-white/10 transition-all duration-500 hover:scale-105 hover:shadow-white/5 text-left flex flex-col justify-between w-full md:w-72 h-64"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                        <div className="relative z-10">
                            <div className="w-12 h-12 rounded-xl bg-neutral-900 border border-white/10 flex items-center justify-center mb-4 shadow-inner group-hover:border-white/30 transition-colors">
                                <FaFileUpload className="h-5 w-5 text-white" />
                            </div>
                            <h2 className="text-lg font-bold mb-2 text-white group-hover:text-white/90 transition-colors">Upload & Summary</h2>
                            <p className="text-neutral-400 group-hover:text-neutral-300 transition-colors text-xs leading-relaxed">
                                Instant analysis. Upload PDFs/images for concise summaries.
                            </p>
                        </div>

                        <div className="relative z-10 flex items-center text-white/50 font-medium group-hover:text-white transition-colors mt-auto">
                            <span className="uppercase tracking-widest text-[10px]">Start Upload</span>
                            <FaArrowRight className="h-3 w-3 ml-2 transform group-hover:translate-x-1 transition-transform" />
                        </div>
                    </button>

                    {/* CTA 2: Chat Assistant */}
                    <button
                        onClick={() => navigate('/chat')}
                        className="group relative overflow-hidden rounded-2xl glass-card p-6 hover:bg-white/10 transition-all duration-500 hover:scale-105 hover:shadow-white/5 text-left flex flex-col justify-between w-full md:w-72 h-64"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                        <div className="relative z-10">
                            <div className="w-12 h-12 rounded-xl bg-neutral-900 border border-white/10 flex items-center justify-center mb-4 shadow-inner group-hover:border-white/30 transition-colors">
                                <FaBalanceScale className="h-5 w-5 text-white" />
                            </div>
                            <h2 className="text-lg font-bold mb-2 text-white group-hover:text-white/90 transition-colors">AI Legal Assistant</h2>
                            <p className="text-neutral-400 group-hover:text-neutral-300 transition-colors text-xs leading-relaxed">
                                Chat with AI to navigate the BNS and IPC regulations.
                            </p>
                        </div>

                        <div className="relative z-10 flex items-center text-white/50 font-medium group-hover:text-white transition-colors mt-auto">
                            <span className="uppercase tracking-widest text-[10px]">Start Chat</span>
                            <FaArrowRight className="h-3 w-3 ml-2 transform group-hover:translate-x-1 transition-transform" />
                        </div>
                    </button>

                </div>

                {/* Scroll Indicator */}
                <div className="animate-bounce text-neutral-600 hidden md:block mb-12">
                    <FaHistory size={20} />
                </div>

                {/* Timeline Section - Navbar Style */}
                <div className="w-full max-w-6xl mb-32 relative z-10">
                    <div className="flex items-center gap-4 mb-8 justify-center">
                        <div className="h-px bg-white/10 w-12"></div>
                        <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400 flex items-center gap-2 uppercase tracking-widest">
                            <FaGavel className="text-blue-400" /> Landmark Judgments
                        </h2>
                        <div className="h-px bg-white/10 w-12"></div>
                    </div>

                    {/* Years Navbar */}
                    <div className="glass-card p-2 rounded-2xl border border-white/5 flex flex-wrap justify-center gap-2 relative">
                        {landmarkCases.map((item, index) => (
                            <div key={index} className="group relative">
                                {/* Year Button */}
                                <button className="px-6 py-3 rounded-xl text-sm font-bold text-neutral-400 hover:text-white hover:bg-white/10 transition-all border border-transparent hover:border-white/5 group-hover:text-white group-hover:bg-white/10 group-hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]">
                                    {item.year}
                                </button>

                                {/* Dropdown / Expanded Row */}
                                <div className="absolute left-1/2 -translate-x-1/2 top-full mt-4 w-80 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-30 transform group-hover:translate-y-0 translate-y-2 pointer-events-none group-hover:pointer-events-auto">
                                    {/* Connectivity Line */}
                                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-0.5 h-4 bg-gradient-to-b from-white/10 to-blue-500/50"></div>
                                    <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_10px_#3b82f6]"></div>

                                    <div className="bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-2xl overflow-hidden backdrop-blur-3xl relative">
                                        {/* Glow effect */}
                                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 to-purple-600"></div>

                                        <div className="p-1 max-h-[60vh] overflow-y-auto custom-scrollbar">
                                            {item.cases.map((caseItem, idx) => (
                                                <button
                                                    key={idx}
                                                    onClick={() => navigate('/chat', { state: { query: caseItem.query } })}
                                                    className="w-full text-left p-4 hover:bg-white/5 transition-colors border-b border-white/5 last:border-0 group/card"
                                                >
                                                    <div className="flex items-start justify-between gap-2 mb-1">
                                                        <h3 className="text-white font-semibold text-sm group-hover/card:text-blue-400 transition-colors leading-tight">
                                                            {caseItem.title}
                                                        </h3>
                                                        <FaExternalLinkAlt className="text-white/20 w-3 h-3 flex-shrink-0 mt-1 opacity-0 group-hover/card:opacity-100 transition-opacity" />
                                                    </div>
                                                    <p className="text-neutral-500 text-xs leading-relaxed line-clamp-3">
                                                        {caseItem.desc}
                                                    </p>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Top 5 Genres Section */}
                <div className="w-full max-w-6xl mb-32 relative z-10">
                    <div className="flex items-center gap-4 mb-12 justify-center">
                        <div className="h-px bg-white/10 w-12"></div>
                        <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-200 to-yellow-400 flex items-center gap-2 uppercase tracking-widest text-center">
                            <FaChartLine className="text-yellow-400" /> Top 5 Legal Genres (By Volume)
                        </h2>
                        <div className="h-px bg-white/10 w-12"></div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {topGenres.map((genre, index) => (
                            <div key={index} className={`relative group glass-card rounded-2xl p-6 border border-white/5 overflow-hidden hover:bg-white/5 transition-all duration-500 ${index === 0 ? 'md:col-span-2 lg:col-span-1 bg-gradient-to-br from-white/5 to-transparent' : ''}`}>
                                {/* Gradient Blob */}
                                <div className={`absolute -right-10 -top-10 w-32 h-32 bg-gradient-to-br ${genre.color} opacity-20 blur-3xl rounded-full group-hover:opacity-30 transition-opacity`}></div>

                                <div className="relative z-10">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl bg-gradient-to-br ${genre.color} text-white shadow-lg`}>
                                            {genre.icon}
                                        </div>
                                        <div className="text-right">
                                            <span className="block text-3xl font-black text-white/90">{genre.rank}</span>
                                            <span className={`text-xs font-bold bg-gradient-to-r ${genre.color} bg-clip-text text-transparent`}>RANK</span>
                                        </div>
                                    </div>

                                    <h3 className="text-lg font-bold text-white mb-2">{genre.title}</h3>
                                    <p className="text-neutral-400 text-sm mb-4 min-h-[40px]">{genre.desc}</p>

                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between text-xs font-medium">
                                            <span className="text-neutral-500">Volume</span>
                                            <span className="text-white bg-white/10 px-2 py-1 rounded">{genre.volume}</span>
                                        </div>

                                        <div className="border-t border-white/10 pt-3">
                                            <p className="text-[10px] uppercase tracking-widest text-neutral-500 mb-2">Common Issues</p>
                                            <div className="flex flex-wrap gap-2">
                                                {genre.issues.map((issue, i) => (
                                                    <span key={i} className="text-[10px] px-2 py-1 rounded bg-black/40 text-neutral-300 border border-white/5">
                                                        {issue}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="border-t border-white/10 pt-3 mt-2">
                                            <div className="flex items-start gap-2">
                                                <FaChartLine className="text-green-400 mt-0.5 text-xs" />
                                                <p className="text-xs text-green-200/80 italic">{genre.trend}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <footer className="w-full flex justify-center pointer-events-none pb-12">
                    <div className="glass px-6 py-3 rounded-full flex items-center gap-6 text-neutral-400 text-xs font-medium tracking-widest uppercase pointer-events-auto shadow-2xl shadow-black/50">
                        <span className="opacity-60">Is This Legal?</span>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <Link to="https://github.com/yking-ly/NineToFive" className="opacity-60">NineToFive</Link>
                        <span className="w-0.5 h-3 bg-white/10 rounded-full"></span>
                        <Link to="/how-to-use" className="text-white/80 hover:text-white transition-colors hover:underline decoration-white/30 underline-offset-4">How to Use</Link>
                    </div>
                </footer>
            </div>
        </div>
    )
}
