import uuid
import sqlite3
import datetime
from database import init_db, get_db_connection
from utils.auth import hash_password
from utils.logger import log_info, log_success, log_error

def get_tailored_tasks(slug, title):
    """
    Returns a customized list of 4 weekly tasks (Title, Objective, Deliverables, Key Steps, Evaluation Criteria)
    tailored specifically to the given internship program.
    """
    s = slug.lower()
    
    # 1. Python Backend
    if 'python-backend' in s or ('python' in s and 'backend' in s):
        return [
            ("Week 1: Flask/FastAPI REST API Architecture", "Design modular RESTful API endpoints and SQLite database schema.", "API Architecture PDF report & Swagger/OpenAPI documentation.", "1. Define Flask Blueprints / FastAPI routers, 2. Create database models, 3. Set up JSON response formats.", "Clean modular code structure and proper HTTP status code handling."),
            ("Week 2: User Authentication & JWT Security", "Implement secure user registration, bcrypt password hashing, and JWT authorization.", "Authentication module code submission & Postman test collection.", "1. Hash passwords using bcrypt, 2. Issue JWT tokens upon login, 3. Create @jwt_required middleware.", "Zero plaintext password exposure and valid token expiration handling."),
            ("Week 3: Database ORM & Asynchronous Processing", "Integrate SQLAlchemy ORM, database migrations, and background worker threads.", "Database migration scripts & async task execution log PDF.", "1. Write SQLAlchemy models, 2. Execute Alembic/SQLite migrations, 3. Process background emails.", "Normalized database tables and non-blocking asynchronous execution."),
            ("Week 4: Production Deployment & API Testing", "Containerize backend service and deploy with Gunicorn / Uvicorn server.", "Production deployment URL, Dockerfile, & final capstone PDF report.", "1. Write Dockerfile, 2. Configure Gunicorn server, 3. Run automated PyTest suite.", "Passing unit test suite, low latency API response, and clean documentation.")
        ]
        
    # 2. Java Enterprise
    elif 'java-enterprise' in s or ('java' in s and 'enterprise' in s):
        return [
            ("Week 1: Spring Boot Application Setup", "Construct Spring Boot Maven/Gradle project architecture and REST Controllers.", "Spring Boot project repository link & REST API documentation PDF.", "1. Configure pom.xml dependencies, 2. Create @RestController endpoints, 3. Set up application.properties.", "Clean Java code formatting and proper dependency injection."),
            ("Week 2: Hibernate ORM & Spring Data JPA", "Model relational database entities and write Spring Data JPA Repositories.", "Entity relational diagram & Repository unit test PDF report.", "1. Annotate @Entity classes, 2. Extend JpaRepository interface, 3. Write custom JPQL queries.", "Proper database relationship mapping (OneToMany, ManyToOne) and zero lazy loading exceptions."),
            ("Week 3: Spring Security & JWT Authorization", "Secure REST endpoints with Spring Security filter chain and JWT Bearer tokens.", "Security Configuration class code & JWT authentication test report.", "1. Configure SecurityFilterChain, 2. Build JwtAuthenticationFilter, 3. Handle Unauthorized exceptions.", "Robust endpoint protection and role-based access control (RBAC)."),
            ("Week 4: Microservices & Docker Deployment", "Containerize Spring Boot app and configure Docker Compose with PostgreSQL.", "Docker Compose configuration & containerized deployment PDF summary.", "1. Create multi-stage Dockerfile, 2. Write docker-compose.yml, 3. Run integration tests.", "Successful container deployment, zero build errors, and verified database persistence.")
        ]

    # 3. C++ Systems Programming
    elif 'cpp' in s or 'c++' in s:
        return [
            ("Week 1: Custom Dynamic Memory Allocator", "Implement custom malloc/free block structures and pointer arithmetic in C++.", "C++ source code submission & Valgrind memory leak report PDF.", "1. Allocate heap memory blocks, 2. Manage free lists, 3. Track memory fragmentation.", "Zero memory leaks, correct pointer manipulation, and clean C++17 syntax."),
            ("Week 2: Object-Oriented System Architecture", "Build template classes, RAII smart pointers (std::unique_ptr, std::shared_ptr).", "Class diagram & System architecture implementation PDF.", "1. Implement RAII resource management, 2. Write template data structures, 3. Overload operators.", "Exception-safe C++ code and optimal memory ownership semantics."),
            ("Week 3: Multithreading & Synchronization", "Create thread pool worker queue using std::thread, std::mutex, and condition variables.", "Multithreaded benchmark report & deadlock analysis PDF.", "1. Spawn worker threads, 2. Synchronize shared queue with std::mutex, 3. Benchmark throughput.", "Thread safety, zero race conditions, and demonstrated CPU core utilization."),
            ("Week 4: System Performance Optimization", "Profile CPU cache usage and optimize low-level data structures.", "Performance profiling report PDF & final compiled binary summary.", "1. Run gprof / Valgrind Callgrind, 2. Eliminate cache misses, 3. Execute Google Benchmark suite.", "Demonstrated speedup over baseline and clean compilation under -Wall -Wextra.")
        ]

    # 4. Go Backend
    elif 'go-' in s or 'golang' in s or 'go ' in title.lower():
        return [
            ("Week 1: Go Project Structure & Standard Library", "Set up idiomatic Go module, package structure, and HTTP standard library routes.", "Go codebase repository & API design specification PDF.", "1. Initialize go.mod, 2. Structure package layout (cmd, pkg, internal), 3. Handle JSON encoding.", "Idiomatic Go code formatting (gofmt) and proper error handling."),
            ("Week 2: Gin Web Framework & GORM Integration", "Build high-speed RESTful microservices using Gin-gonic and GORM database ORM.", "REST API documentation PDF & GORM database migration logs.", "1. Configure Gin router, 2. Define GORM structs, 3. Implement CRUD database handlers.", "Low latency API responses and clean database transaction management."),
            ("Week 3: Concurrency with Goroutines & Channels", "Implement concurrent background task processors using Goroutines and Channels.", "Concurrency benchmark report & Worker pool implementation PDF.", "1. Spawn worker goroutines, 2. Manage buffered channels, 3. Prevent goroutine leaks with context.", "Safe concurrent execution, zero data races (verified via go test -race)."),
            ("Week 4: gRPC Microservices & Dockerization", "Build gRPC service with Protocol Buffers and build lightweight Alpine Docker image.", "Protobuf definitions (.proto), gRPC client test, & Docker deployment PDF.", "1. Write .proto service schema, 2. Generate Go gRPC code, 3. Package 15MB scratch Docker image.", "High-throughput gRPC communication and minimal Docker image footprint.")
        ]

    # 5. Node.js & JavaScript Backend
    elif 'node' in s or 'express' in s:
        return [
            ("Week 1: Express.js Architecture & Middleware", "Build scalable Express.js server layout with custom error handling middleware.", "Express.js codebase & API route documentation PDF.", "1. Configure express.Router(), 2. Add helmet & cors middleware, 3. Create centralized error handler.", "Clean asynchronous error catching and modular route structure."),
            ("Week 2: MongoDB & Mongoose Schemas", "Model MongoDB collections, write Mongoose schemas, and implement data validation.", "Mongoose Data Schema Specification PDF & MongoDB query logs.", "1. Define Schema types & validations, 2. Write aggregation pipelines, 3. Index frequent query fields.", "Efficient database indexing and strict schema data validation."),
            ("Week 3: JWT Security & Input Sanitization", "Secure endpoints with JWT Bearer tokens, express-validator, and rate limiting.", "Security Audit Report PDF & Postman test collection.", "1. Hash passwords with bcryptjs, 2. Sanitize user inputs, 3. Implement express-rate-limit.", "Protection against NoSQL injection and rate limit compliance."),
            ("Week 4: Socket.io & PM2 Production Deploy", "Add real-time WebSockets with Socket.io and deploy using PM2 process manager.", "Live production URL & Socket.io event test documentation PDF.", "1. Set up Socket.io connection handlers, 2. Configure PM2 cluster mode, 3. Deploy to cloud server.", "Zero downtime cluster reload and active real-time WebSocket communication.")
        ]

    # 6. React.js Frontend
    elif 'react' in s and 'native' not in s:
        return [
            ("Week 1: React Component Architecture & JSX", "Design modular component hierarchy, custom CSS modules, and responsive layouts.", "React Component Tree diagram & UI wireframe documentation PDF.", "1. Build reusable UI components, 2. Apply CSS module styles, 3. Manage local component state.", "Clean JSX formatting, modular styling, and 100% viewport responsiveness."),
            ("Week 2: Advanced React Hooks & Context API", "Implement custom React hooks (useFetch, useLocalStorage) and global Context API state.", "Hooks implementation codebase & State flow diagram PDF.", "1. Write custom custom hooks, 2. Create React.createContext provider, 3. Optimize render cycles.", "Zero unnecessary component re-renders and clean state management."),
            ("Week 3: REST API Integration & React Router", "Connect React app to backend REST API endpoints using Axios and React Router DOM v6.", "API Integration test report & Client-side routing specification PDF.", "1. Configure Hash/BrowserRouter, 2. Handle loading & error UI states, 3. Intercept HTTP requests.", "Seamless SPA page transitions and robust network error recovery."),
            ("Week 4: Performance Optimization & Deployment", "Optimize bundle size with code splitting (React.lazy), Suspense, and deploy to Vercel.", "Production Vercel deployment URL & Lighthouse Performance Audit PDF.", "1. Implement dynamic imports, 2. Audit bundle with Webpack Analyzer, 3. Deploy build static files.", "Lighthouse score > 90, low First Contentful Paint (FCP), and zero console errors.")
        ]

    # 7. Vue.js Frontend
    elif 'vue' in s:
        return [
            ("Week 1: Vue 3 Composition API Setup", "Build Single File Components (SFC) using Vue 3 Composition API and Script Setup.", "Vue 3 project repository & Component layout PDF report.", "1. Configure Vite + Vue 3, 2. Write ref() and reactive() state, 3. Style scoped components.", "Modern Vue 3 syntax and clean component structure."),
            ("Week 2: Vue Router & Pinia State Store", "Implement client-side SPA routing with Vue Router and global state management with Pinia.", "Pinia Store architecture diagram & Router guard documentation PDF.", "1. Define routes and navigation guards, 2. Create Pinia store actions & getters, 3. Persist state.", "Type-safe state management and seamless page transitions."),
            ("Week 3: Axios API Integration & Form Validation", "Fetch remote REST data and validate user forms using VeeValidate / Yup.", "Form Validation test report & API integration logs PDF.", "1. Setup Axios instance, 2. Create custom form validation rules, 3. Render dynamic feedback.", "User-friendly error messages and clean asynchronous data fetching."),
            ("Week 4: Production Build & Netlify Deploy", "Optimize Vite build assets, run unit tests with Vitest, and deploy live to Netlify.", "Live Netlify URL & Vitest test execution report PDF.", "1. Run vitest unit tests, 2. Bundle static assets with Vite, 3. Configure Netlify redirects.", "Passing unit test suite and fast production asset loading.")
        ]

    # 8. Angular Enterprise
    elif 'angular' in s:
        return [
            ("Week 1: Angular Architecture & TypeScript", "Set up Angular CLI project, feature modules, components, and Angular Material UI.", "Angular Module Tree specification PDF & project repository.", "1. Generate feature modules, 2. Apply Angular Material components, 3. Structure TypeScript models.", "Strict TypeScript typing and clean Angular modular structure."),
            ("Week 2: Services & Dependency Injection", "Build injectable Services for business logic and REST data fetching via HttpClient.", "Service architecture diagram & HttpClient test report PDF.", "1. Annotate @Injectable() services, 2. Use HttpClient GET/POST methods, 3. Catch HttpErrorResponse.", "Clean dependency injection and reusable service layers."),
            ("Week 3: RxJS Observables & Reactive Forms", "Master RxJS operators (map, switchMap, catchError) and complex Reactive Form Groups.", "RxJS data stream flow PDF & Form validation test suite.", "1. Build FormGroup & FormControls, 2. Pipe RxJS operators, 3. Implement custom AsyncValidators.", "Reactive data handling without memory leaks (unsubscribe / takeUntil)."),
            ("Week 4: NgRx State & Production Deployment", "Manage global state using NgRx Store, Actions, Reducers, Effects, and deploy to AWS S3.", "Live Deployment URL & NgRx Store state tree PDF documentation.", "1. Define NgRx actions & reducers, 2. Handle side-effects with @Effect, 3. Build AOT production bundle.", "Ahead-of-Time (AOT) compiled production build with optimized bundle size.")
        ]

    # 9. TypeScript & JS
    elif 'typescript' in s or 'javascript' in s:
        return [
            ("Week 1: TypeScript Compiler & Type System", "Master TypeScript Interfaces, Generics, Union Types, and tsconfig.json options.", "TypeScript Type Definition spec PDF & source code.", "1. Configure strict tsconfig, 2. Define custom type interfaces, 3. Implement generic functions.", "Zero 'any' type usages and 100% strict type check compilation."),
            ("Week 2: Asynchronous JS & Event Loop", "Deep dive into Promises, Async/Await, Microtasks vs Macrotasks, and Event Loop mechanics.", "Async execution analysis PDF & Promise test suite.", "1. Write custom Promise wrappers, 2. Handle concurrent Promise.all Settled, 3. Benchmark event loop.", "Clean asynchronous control flow without unhandled promise rejections."),
            ("Week 3: Type-safe API Client & Zod", "Build robust API HTTP client with automatic Zod schema parsing and runtime validation.", "API Client SDK codebase & Zod schema validation report PDF.", "1. Define Zod validation schemas, 2. Parse API response JSON, 3. Infer TypeScript types.", "Runtime type safety preventing invalid API payloads."),
            ("Week 4: Webpack/Vite Asset Bundling & NPM", "Bundle JavaScript library using Vite/Webpack and publish type declaration files (.d.ts).", "NPM package package.json specification & bundle audit PDF.", "1. Configure Webpack/Vite library mode, 2. Generate declaration files, 3. Run Tree-shaking audit.", "Compact bundled distribution files with full TypeScript autocomplete support.")
        ]

    # 10. Next.js & React Ecosystem
    elif 'nextjs' in s or 'next' in s:
        return [
            ("Week 1: Next.js App Router & Server Components", "Build modern Next.js 14 applications using App Router, React Server Components (RSC).", "App Router layout architecture diagram & codebase PDF.", "1. Organize app/ directory routes, 2. Differentiate Server vs Client components, 3. Add loading.tsx.", "Optimal Server-Side Rendering (SSR) and fast initial page loads."),
            ("Week 2: Server Actions & Prisma ORM", "Implement Next.js Server Actions for form submissions and query database via Prisma ORM.", "Prisma Schema definition & Server Action test log PDF.", "1. Define prisma.schema models, 2. Write asynchronous Server Actions, 3. Revalidate cache tags.", "Type-safe database queries without client-side API boilerplate."),
            ("Week 3: NextAuth.js & Middleware Security", "Secure routes with NextAuth.js (Auth.js) supporting OAuth Providers and Credentials login.", "Security Middleware configuration & Auth test report PDF.", "1. Configure NextAuth options, 2. Add auth middleware guards, 3. Manage JWT session tokens.", "Protected server routes and seamless user authentication flow."),
            ("Week 4: Image Optimization & Vercel Deploy", "Optimize images with next/image, add OpenGraph metadata, and deploy live on Vercel Edge.", "Live Vercel deployment URL & Lighthouse Audit report PDF.", "1. Configure next/image loaders, 2. Add dynamic metadata tags, 3. Deploy to Vercel global edge.", "Lighthouse Performance score > 95 and instant global CDN delivery.")
        ]

    # 11. Flutter Mobile App
    elif 'flutter' in s:
        return [
            ("Week 1: Flutter Widgets & Dart Syntax", "Master Dart OOP syntax, Stateless vs Stateful Widgets, and MaterialApp responsive UI.", "Flutter App UI Screenshots & Widget Tree PDF report.", "1. Lay out Scaffolds, Rows, Columns, 2. Implement custom Widget themes, 3. Handle touch inputs.", "Pixel-perfect mobile UI conforming to Material 3 guidelines."),
            ("Week 2: State Management with BLoC / Provider", "Manage application state using Provider or Flutter BLoC architecture.", "State Architecture diagram & BLoC event test log PDF.", "1. Define BLoC Events & States, 2. Wrap UI in BlocBuilder, 3. Handle asynchronous state changes.", "Clean separation of business logic from UI layer."),
            ("Week 3: REST API & SQLite Local Database", "Fetch remote JSON data with http package and persist local data using sqflite.", "API Integration codebase & sqflite database schema PDF.", "1. Parse JSON models, 2. Cache offline data in SQLite, 3. Display pull-to-refresh list.", "Offline-first mobile user experience with automatic background sync."),
            ("Week 4: Native Plugins & Release Build", "Integrate native device plugins (Camera, Location) and generate signed Android APK / iOS ipa.", "Signed APK release package & App Store submission PDF checklist.", "1. Configure AndroidManifest & Info.plist, 2. Sign APK release build, 3. Run Flutter Integration Test.", "Zero native crashes and verified signed APK production file.")
        ]

    # 12. iOS Swift
    elif 'ios' in s or 'swift' in s:
        return [
            ("Week 1: Swift 5 Language & SwiftUI UI", "Learn Swift 5 language features (Optionals, Structs, Enums) and build SwiftUI layouts.", "SwiftUI screen wireframes & Xcode project repository link.", "1. Lay out SwiftUI Views, 2. Bind @State and @Binding variables, 3. Apply view modifiers.", "Clean Swift syntax and responsive iOS interface layouts."),
            ("Week 2: SwiftUI State & Navigation", "Implement complex navigation flows with NavigationStack and @StateObject view models.", "App Navigation Flowchart & ViewModel architecture PDF.", "1. Implement MVVM pattern, 2. Handle list selection & sheets, 3. Pass environment objects.", "Predictable data flow without memory reference cycles."),
            ("Week 3: URLSession REST & CoreData", "Fetch remote RESTful endpoints with URLSession async/await and persist data with CoreData.", "Network Layer codebase & CoreData ERD PDF specification.", "1. Construct Codable struct models, 2. Fetch JSON asynchronously, 3. Save entities in CoreData.", "Robust network error handling and local data persistence."),
            ("Week 4: TestFlight Deployment & App Store", "Perform unit testing with XCTest, profile memory with Instruments, and prepare TestFlight build.", "TestFlight build confirmation screenshot & XCTest report PDF.", "1. Run XCTest unit tests, 2. Profile memory leaks in Xcode Instruments, 3. Export IPA archive.", "Passing test suite and clean Xcode archive compilation.")
        ]

    # 13. Android Kotlin
    elif 'android' in s or ('kotlin' in s and 'backend' not in s):
        return [
            ("Week 1: Kotlin & Jetpack Compose UI", "Master Kotlin syntax (Coroutines, Extensions) and build declarative UI with Jetpack Compose.", "Jetpack Compose Screen Layouts PDF report & Android repository.", "1. Write Composables (@Composable), 2. Style Material 3 themes, 3. Manage Compose state.", "Declarative Kotlin UI layout matching Material Design 3 guidelines."),
            ("Week 2: ViewModel & LiveData / Flow", "Implement MVVM architecture with Jetpack ViewModel and Kotlin StateFlow.", "MVVM Architecture diagram & ViewModel test log PDF.", "1. Extend ViewModel class, 2. Emit StateFlow events, 3. Handle configuration changes.", "Preserved UI state across device screen rotations."),
            ("Week 3: Retrofit HTTP & Room SQLite", "Consume REST web services via Retrofit 2 and cache data in Room Database.", "Network & Database Layer codebase PDF & Room migration logs.", "1. Define Retrofit interface, 2. Write Room @Entity and @Dao, 3. Execute repository queries.", "Smooth offline caching and background thread execution."),
            ("Week 4: APK Signing & Google Play Release", "Run Android Lint checks, generate signed release App Bundle (AAB), and audit permissions.", "Signed Android App Bundle (AAB) file & Google Play Console checklist PDF.", "1. Optimize ProGuard / R8 obfuscation, 2. Generate signed release AAB, 3. Audit AndroidManifest.", "Verified signed AAB file ready for Google Play Store upload.")
        ]

    # 14. AI & Machine Learning
    elif 'ai' in s or 'ml' in s or 'machine-learning' in s or 'deep-learning' in s:
        return [
            ("Week 1: Data Preprocessing & Feature Engineering", "Clean complex datasets, handle missing values, encode categorical features using Scikit-Learn.", "Data Cleaning Pipeline PDF report & Jupyter Notebook codebase.", "1. Impute missing data, 2. Apply One-Hot & Label Encoding, 3. Scale numeric features (StandardScaler).", "Clean dataset pipeline with zero data leakage."),
            ("Week 2: Supervised Learning & Evaluation Metrics", "Train Classification (Random Forest, XGBoost) and Regression models; evaluate ROC-AUC.", "Model Performance Evaluation PDF with Confusion Matrix & ROC plots.", "1. Split Train/Test sets, 2. Fit Scikit-Learn classifiers, 3. Compute Precision, Recall, F1-Score.", "Rigorous model validation and clear performance visualization."),
            ("Week 3: Deep Neural Networks with PyTorch/TensorFlow", "Construct multi-layer artificial neural networks (ANN) and optimize with Adam/SGD.", "Neural Network Training Loss curve plots & PyTorch model definition PDF.", "1. Define PyTorch nn.Module layers, 2. Set up CrossEntropy loss, 3. Plot training/validation loss.", "Demonstrated convergence without overfitting (Dropout & Early Stopping)."),
            ("Week 4: Model Serving via REST API", "Serialize trained machine learning model and serve real-time predictions via Flask API.", "Live Inference REST API specification & Postman JSON test PDF.", "1. Export model using Joblib/ONNX, 2. Build POST /predict endpoint, 3. Validate JSON payload.", "Low-latency prediction response (< 100ms) and robust error handling.")
        ]

    # 15. Data Science & Analytics
    elif 'data-science' in s or 'data-analysis' in s or 'analytics' in s:
        return [
            ("Week 1: Data Wrangling with Pandas & NumPy", "Manipulate raw datasets, perform groupby aggregations, and reshape DataFrames.", "Data Analysis Notebook PDF report & summary statistics table.", "1. Load raw CSV/Parquet files, 2. Perform pivot tables & aggregations, 3. Filter data anomalies.", "Accurate statistical aggregations and clean data structures."),
            ("Week 2: Exploratory Data Analysis & Visualization", "Generate publication-quality charts using Matplotlib, Seaborn, and Plotly.", "Exploratory Data Analysis PDF Report with 10+ interactive charts.", "1. Plot correlation heatmaps, 2. Analyze distributions via box plots, 3. Identify key trends.", "Visually compelling charts clearly communicating business insights."),
            ("Week 3: Statistical Inference & Hypothesis Testing", "Perform A/B test analysis, t-tests, Chi-Square tests, and calculate p-values.", "Statistical Testing Methodology PDF & Hypothesis conclusion report.", "1. Formulate Null & Alternative hypotheses, 2. Execute SciPy stats tests, 3. Calculate 95% CI.", "Statistically sound conclusions supported by empirical p-values."),
            ("Week 4: Business Insights & Executive Dashboard", "Synthesize analytical findings into an executive presentation deck and dashboard.", "Final Business Analytics Deck PDF & Executive Summary Report.", "1. Summarize strategic takeaways, 2. Build interactive dashboard, 3. Formulate recommendations.", "Polished executive presentation with actionable business recommendations.")
        ]

    # 16. AWS / DevOps / Cloud
    elif 'aws' in s or 'cloud' in s or 'devops' in s or 'docker' in s:
        return [
            ("Week 1: Cloud Network Topology & Security", "Configure Virtual Private Cloud (VPC), public/private subnets, Security Groups, and IAM roles.", "VPC Architecture Diagram PDF & Terraform / AWS CLI setup script.", "1. Create VPC with CIDR block, 2. Configure Internet Gateway & Route Tables, 3. Restrict IAM permissions.", "Secure network isolation conforming to AWS Well-Architected Framework."),
            ("Week 2: Compute & Load Balancing", "Provision EC2 compute instances, configure Auto Scaling Groups, and setup Application Load Balancer.", "Compute Infrastructure Setup log & Load Balancer test PDF.", "1. Launch EC2 instances with custom UserData scripts, 2. Attach ALB, 3. Test auto-scaling.", "High availability setup distributing traffic across multi-AZ instances."),
            ("Week 3: Serverless & Storage Infrastructure", "Deploy serverless AWS Lambda functions, S3 storage bucket policies, and CloudFront CDN.", "Serverless Architecture spec & Lambda execution metrics PDF.", "1. Configure S3 bucket encryption & CORS, 2. Write Python AWS Lambda function, 3. Setup CloudFront.", "Serverless execution with low latency global content delivery."),
            ("Week 4: Automated Infrastructure as Code (IaC)", "Automate full cloud stack deployment using Terraform / CloudFormation scripts.", "Terraform Plan output log & Live Cloud Infrastructure PDF verification.", "1. Write Terraform HCL scripts, 2. Execute terraform apply, 3. Verify infrastructure tear-down.", "100% reproducible Infrastructure as Code with zero manual step dependencies.")
        ]

    # 17. Cybersecurity & Ethical Hacking
    elif 'cyber' in s or 'hacking' in s or 'security' in s:
        return [
            ("Week 1: Reconnaissance & Network Auditing", "Perform target subdomain enumeration, service fingerprinting, and Nmap port scanning.", "Network Audit PDF Report & Nmap XML output scan logs.", "1. Run Nmap script scans (-sV -sC), 2. Identify open ports and service versions, 3. Map attack surface.", "Comprehensive network topology breakdown and risk severity scoring."),
            ("Week 2: OWASP Web Vulnerability Assessment", "Identify and exploit OWASP Top 10 vulnerabilities (SQLi, XSS, CSRF, IDOR) in audit lab.", "Vulnerability Assessment Report PDF with Proof-of-Concept payloads.", "1. Intercept HTTP traffic with Burp Suite, 2. Test SQL injection & XSS payloads, 3. Audit auth headers.", "Clear reproduction steps and remediation guidance for each vulnerability."),
            ("Week 3: Traffic Inspection & Malware Analysis", "Analyze network PCAP files using Wireshark to detect malicious command-and-control (C2) traffic.", "Wireshark Traffic Analysis PDF report & Incident Response log.", "1. Filter TCP/UDP streams in Wireshark, 2. Extract plaintext credentials, 3. Identify suspicious DNS queries.", "Accurate threat detection and protocol analysis."),
            ("Week 4: Penetration Test Report & Hardening", "Draft institutional Penetration Testing Summary Report and write security hardening rules.", "Final Executive Penetration Test Report PDF & Remediation Checklist.", "1. Categorize vulnerabilities by CVSS score, 2. Write remediation code fixes, 3. Present executive summary.", "Professional report format suitable for corporate CISO presentation.")
        ]

    # 18. Solidity & Web3
    elif 'solidity' in s or 'blockchain' in s or 'web3' in s:
        return [
            ("Week 1: Solidity Smart Contract Syntax & Hardhat", "Write Solidity 0.8+ contracts, data types, mappings, and set up Hardhat testing environment.", "Solidity Smart Contract source code & Hardhat test suite PDF.", "1. Write contract state variables & functions, 2. Set up Hardhat project, 3. Write Chai unit tests.", "Clean Solidity code compiled without warnings and passing unit tests."),
            ("Week 2: ERC-20 / ERC-721 Token Standards", "Implement ERC-20 token contract with minting, burning, and OpenZeppelin security modules.", "Token Contract Specification PDF & Etherscan Verification logs.", "1. Inherit OpenZeppelin ERC20 contract, 2. Write access control (Ownable), 3. Test token transfers.", "Standard-compliant token implementation passing security audits."),
            ("Week 3: Decentralized Protocol & AMM Logic", "Build Automated Market Maker (AMM) token swap protocol with liquidity pools.", "DeFi Protocol Architecture diagram & Smart Contract audit report PDF.", "1. Implement liquidity provider shares, 2. Write constant-product formula (x*y=k), 3. Prevent reentrancy.", "Secure contract code immune to reentrancy attacks (ReentrancyGuard)."),
            ("Week 4: Testnet Deployment & Web3 DApp Frontend", "Deploy smart contract to Sepolia testnet and connect frontend using Ethers.js / Wagmi.", "Live Testnet Contract Address & Web3 DApp interactive interface PDF.", "1. Compile & deploy to Sepolia testnet, 2. Connect MetaMask wallet, 3. Execute contract transactions.", "Verified contract on Etherscan and functional Web3 wallet integration.")
        ]

    # 19. Game Development (Unity / Unreal)
    elif 'game' in s or 'unity' in s or 'unreal' in s:
        return [
            ("Week 1: Game Mechanics & Physics Setup", "Build player character movement controllers, 2D/3D physics colliders, and camera tracking.", "Game Play Mechanics Demonstration Video/Screenshots & Architecture PDF.", "1. Script player movement & jump mechanics, 2. Configure Rigidbody physics, 3. Implement Cinemachine camera.", "Smooth player controls and accurate physics collision detection."),
            ("Week 2: Game Loop, Enemies & Combat Systems", "Implement enemy AI state machines (Patrol, Chase, Attack), health systems, and combat loops.", "AI State Machine Diagram & Combat Codebase submission PDF.", "1. Script enemy navigation, 2. Handle damage & hitboxes, 3. Manage game manager state.", "Responsive game loop and balanced enemy difficulty curve."),
            ("Week 3: UI Canvas, Audio & Particle Effects", "Design Game HUD (Health bar, Score counter, Inventory), sound effects, and visual particle systems.", "UI & Audio Asset Spec PDF & Gameplay screenshots.", "1. Lay out Unity Canvas / Unreal UI, 2. Trigger audio clips on event, 3. Create particle FX.", "Polished user interface and audio-visual feedback on player actions."),
            ("Week 4: Level Design & Executable Build", "Construct complete playable level, optimize graphics performance, and build standalone executable.", "Playable Game Executable (ZIP/WebGL link) & Game Design Document PDF.", "1. Design level environment, 2. Bake occlusion culling & lighting, 3. Export WebGL / Windows build.", "Playable executable running at stable 60 FPS with zero crash bugs.")
        ]

    # 20. QA & Automation Testing
    elif 'qa' in s or 'testing' in s or 'selenium' in s:
        return [
            ("Week 1: Test Plan & Manual Scenario Design", "Write comprehensive Software Test Plan, Test Cases, and Requirement Traceability Matrix (RTM).", "Software Test Plan & Test Case Specification PDF.", "1. Identify functional test scenarios, 2. Write step-by-step test cases, 3. Map requirement matrix.", "Thorough test coverage including edge cases and negative test scenarios."),
            ("Week 2: Selenium WebDriver & TestNG Framework", "Automate web browser actions using Selenium WebDriver and Page Object Model (POM) pattern.", "Automation Framework codebase & Test Execution Report PDF.", "1. Set up Selenium WebDriver, 2. Create Page Objects, 3. Write TestNG / PyTest assertions.", "Robust element locators (XPath/CSS) and dynamic explicit wait handling."),
            ("Week 3: Data-Driven & API Automation Testing", "Implement Data-Driven testing reading CSV/Excel datasets and automate REST API checks using RestAssured.", "Data-Driven Test Suite codebase & API Test Results PDF.", "1. Read test data from Excel/CSV, 2. Validate API status codes & JSON schemas, 3. Generate HTML reports.", "Automated execution of 50+ test combinations with detailed HTML reporting."),
            ("Week 4: Performance Load Testing & CI/CD", "Execute JMeter performance load tests, analyze response times, and run test suite in Jenkins.", "JMeter Performance Load Audit PDF & Jenkins Pipeline execution logs.", "1. Create JMeter Thread Group, 2. Simulate 100 concurrent users, 3. Integrate test run into CI/CD.", "Clear identification of performance bottlenecks and automated CI/CD integration.")
        ]

    # 21. Default Fallback tailored by Title
    else:
        return [
            (f"Week 1: Fundamentals of {title}", f"Master foundational concepts, set up development environment, and analyze project requirements for {title}.", f"Environment Setup Guide & Initial Architecture Document PDF for {title}.", f"1. Install required toolchains for {title}, 2. Configure IDE/workspace, 3. Build initial prototype framework.", f"Clean environment setup, clear documentation, and valid project structure."),
            (f"Week 2: Core Feature Implementation", f"Develop primary functional components and business logic for {title}.", f"Source Code Repository & Core Feature Verification PDF Report for {title}.", f"1. Implement core modules, 2. Handle data input & processing, 3. Execute functional testing.", f"Well-structured code, zero syntax errors, and verified feature behavior."),
            (f"Week 3: Advanced Integration & Refactoring", f"Integrate secondary modules, optimize system performance, and refactor codebase for {title}.", f"Integration Test Suite & Code Quality Audit PDF Report for {title}.", f"1. Connect system components, 2. Refactor complex logic, 3. Run automated regression checks.", f"Robust module integration, zero regression bugs, and clean code formatting."),
            (f"Week 4: Final Capstone & Executive Presentation", f"Finalize capstone project, draft comprehensive documentation, and prepare executive deployment package for {title}.", f"Final Capstone Deliverable Package PDF & Live Demonstration Link for {title}.", f"1. Write final project documentation, 2. Conduct end-to-end verification, 3. Generate final summary PDF.", f"100% project completion, professional documentation quality, and successful final review.")
        ]

def seed_database():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    log_info("Seeding database with default admin, 20 sectors, and 70+ virtual internships with TAILORED 4-week task blueprints...")

    # 1. Seed Admin
    cursor.execute("SELECT id FROM admins WHERE email = 'admin@webintern.com'")
    if not cursor.fetchone():
        admin_id = str(uuid.uuid4())
        pw_hash = hash_password("admin123")
        cursor.execute(
            "INSERT INTO admins (id, email, password_hash, full_name) VALUES (?, 'admin@webintern.com', ?, 'System Administrator')",
            (admin_id, pw_hash)
        )
        log_success("Created default admin: admin@webintern.com / admin123")

    # 2. Seed 20 Sectors
    sectors_data = [
        ("Engineering & Technology", "engineering-technology", "💻", "Software development, web development, mobile apps, cloud computing, AI/ML"),
        ("Data Science & Analytics", "data-science-analytics", "📊", "Data analysis, business intelligence, statistical analysis, big data"),
        ("Cybersecurity", "cybersecurity", "🛡️", "Network security, ethical hacking, penetration testing, security infrastructure"),
        ("DevOps & Cloud", "devops-cloud", "☁️", "AWS, Azure, GCP, Kubernetes, Docker, CI/CD pipelines"),
        ("Frontend Development", "frontend-development", "🖥️", "React, Vue, Angular, HTML/CSS, JavaScript, UI/UX"),
        ("Backend Development", "backend-development", "🗄️", "Node.js, Django, Spring, FastAPI, databases, APIs"),
        ("Mobile App Development", "mobile-app-development", "📱", "iOS, Android, React Native, Flutter, cross-platform"),
        ("Artificial Intelligence & ML", "ai-machine-learning", "🧠", "Machine learning, deep learning, NLP, computer vision, TensorFlow"),
        ("Blockchain & Web3", "blockchain-web3", "🔗", "Solidity, smart contracts, DeFi, cryptocurrencies, blockchain"),
        ("Game Development", "game-development", "🎮", "Unity, Unreal Engine, game design, graphics programming"),
        ("Quality Assurance & Testing", "qa-testing", "✅", "Automation testing, manual testing, performance testing, QA"),
        ("Business & Management", "business-management", "💼", "Business analysis, project management, product management, strategy"),
        ("Marketing & Digital", "marketing-digital", "📈", "Digital marketing, SEO, content marketing, social media"),
        ("Finance & Banking", "finance-banking", "💳", "Fintech, financial analysis, trading, banking systems"),
        ("Design & UX/UI", "design-ux-ui", "🎨", "UI/UX design, graphic design, interaction design, prototyping"),
        ("Science", "science", "🔬", "Data Science, Research, Physics, and Chemical Analysis tracks."),
        ("Medical & Healthcare", "medical-healthcare", "🏥", "Health Informatics, Clinical Research, and Biotech tracks."),
        ("Law & Legal Studies", "law-legal-studies", "⚖️", "Corporate Law, Cyber Law, and Legal Research tracks."),
        ("Humanities & Social Sciences", "humanities-social-sciences", "📖", "Psychology, Sociology, Content Writing, and International Relations."),
        ("Agriculture & Environmental", "agriculture-environmental", "🌿", "Agritech, Environmental Impact, and Sustainable Systems.")
    ]

    sector_map = {}
    for name, slug, emoji, desc in sectors_data:
        cursor.execute("SELECT id FROM sectors WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        if row:
            sector_map[slug] = row['id']
            cursor.execute("UPDATE sectors SET name = ?, icon_url = ?, description = ? WHERE id = ?", (name, emoji, desc, row['id']))
        else:
            sec_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO sectors (id, name, slug, icon_url, description) VALUES (?, ?, ?, ?, ?)",
                (sec_id, name, slug, emoji, desc)
            )
            sector_map[slug] = sec_id

    # Fetch existing internships or list of 70+ internships
    cursor.execute("SELECT id, title, slug FROM internships")
    existing_internships = [dict(r) for r in cursor.fetchall()]

    log_info(f"Assigning tailored 4-week task blueprints for {len(existing_internships)} internships...")

    task_count = 0
    for intern in existing_internships:
        intern_id = intern['id']
        title = intern['title']
        slug = intern['slug']

        # Clear existing generic tasks for clean refresh
        cursor.execute("DELETE FROM internship_tasks WHERE internship_id = ?", (intern_id,))

        tasks_data = get_tailored_tasks(slug, title)

        for week_num, (t_title, t_obj, t_deliv, t_steps, t_crit) in enumerate(tasks_data, start=1):
            cursor.execute("""
                INSERT INTO internship_tasks (
                    id, internship_id, week_number, title, objective, deliverables, key_steps, evaluation_criteria
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), intern_id, week_num, t_title, t_obj, t_deliv, t_steps, t_crit))
            task_count += 1

    conn.commit()
    conn.close()
    log_success(f"Seeding completed successfully! Assigned {task_count} tailored 4-week task blueprints across all internships.")

if __name__ == '__main__':
    seed_database()
