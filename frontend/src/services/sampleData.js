// =====================================================================
// TEMPORARY SAMPLE DATA (Phase 2 only)
// In Phase 3/4 this data will come from the FastAPI backend and SQLite.
// The pages never import this file directly. They use services/api.js.
// =====================================================================

// ---------- The three supported careers ----------
export const careers = [
  {
    id: 'full-stack',
    name: 'Full Stack Developer',
    icon: '💻',
    description:
      'Build complete web applications: the screens users see, the server that runs the logic, and the database that stores the data.',
  },
  {
    id: 'data-analyst',
    name: 'Data Analyst',
    icon: '📊',
    description:
      'Collect, clean, and analyze data, then turn it into charts and reports that help people make better decisions.',
  },
  {
    id: 'ai-ml',
    name: 'AI/ML Engineer',
    icon: '🤖',
    description:
      'Prepare data, train and evaluate machine learning models, and get them ready to be used in real applications.',
  },
];

// ---------- Skill catalog: each skill is stored ONCE ----------
// hoursPerLevel = average hours to move up one proficiency level (from Phase 1)
export const skillCatalog = {
  html: {
    name: 'HTML', hoursPerLevel: 8,
    objective: 'Build well-structured web pages using semantic HTML, forms, and accessibility basics.',
    resource: { title: 'W3Schools HTML Tutorial', url: 'https://www.w3schools.com/html/' },
  },
  css: {
    name: 'CSS', hoursPerLevel: 10,
    objective: 'Style responsive layouts using Flexbox, Grid, and media queries.',
    resource: { title: 'W3Schools CSS Tutorial', url: 'https://www.w3schools.com/css/' },
  },
  javascript: {
    name: 'JavaScript', hoursPerLevel: 20,
    objective: 'Write modern JavaScript to handle events, change the page, and fetch data from APIs.',
    resource: { title: 'The Modern JavaScript Tutorial', url: 'https://javascript.info/' },
  },
  git: {
    name: 'Git & GitHub', hoursPerLevel: 6,
    objective: 'Track code changes with Git and collaborate using branches and pull requests on GitHub.',
    resource: { title: 'Pro Git Book (free)', url: 'https://git-scm.com/book/en/v2' },
  },
  react: {
    name: 'React', hoursPerLevel: 20,
    objective: 'Build reusable components using props, state, hooks, and routing.',
    resource: { title: 'React Official Learn Guide', url: 'https://react.dev/learn' },
  },
  node: {
    name: 'Node.js & Express', hoursPerLevel: 18,
    objective: 'Create a web server with Node.js and Express using routes and middleware.',
    resource: { title: 'Node.js Official Learn', url: 'https://nodejs.org/en/learn' },
  },
  sql: {
    name: 'SQL', hoursPerLevel: 15,
    objective: 'Design tables and write queries using SELECT, JOIN, GROUP BY, and subqueries.',
    resource: { title: 'SQLBolt Interactive Lessons', url: 'https://sqlbolt.com/' },
  },
  rest: {
    name: 'REST APIs', hoursPerLevel: 10,
    objective: 'Design and use REST APIs with HTTP methods, status codes, and JSON.',
    resource: { title: 'REST API Tutorial', url: 'https://restfulapi.net/' },
  },
  auth: {
    name: 'Authentication & Security Basics', hoursPerLevel: 8,
    objective: 'Add login with password hashing and tokens, and protect against common web attacks.',
    resource: { title: 'OWASP Top Ten', url: 'https://owasp.org/www-project-top-ten/' },
  },
  testing: {
    name: 'Testing & Debugging', hoursPerLevel: 8,
    objective: 'Find bugs using browser developer tools and write simple automated tests.',
    resource: { title: 'Jest Getting Started', url: 'https://jestjs.io/docs/getting-started' },
  },
  excel: {
    name: 'Excel', hoursPerLevel: 10,
    objective: 'Use formulas, lookups, pivot tables, and charts to analyze data in Excel.',
    resource: { title: 'Microsoft Excel Help & Training', url: 'https://support.microsoft.com/en-us/excel' },
  },
  python: {
    name: 'Python', hoursPerLevel: 20,
    objective: 'Write Python programs using data types, loops, functions, and files.',
    resource: { title: 'Official Python Tutorial', url: 'https://docs.python.org/3/tutorial/' },
  },
  pandas: {
    name: 'Pandas & NumPy', hoursPerLevel: 15,
    objective: 'Load, filter, group, and summarize data using Pandas and NumPy.',
    resource: { title: 'Pandas Getting Started Tutorials', url: 'https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html' },
  },
  statistics: {
    name: 'Statistics', hoursPerLevel: 15,
    objective: 'Understand averages, spread, probability, and hypothesis testing for data decisions.',
    resource: { title: 'Khan Academy Statistics & Probability', url: 'https://www.khanacademy.org/math/statistics-probability' },
  },
  cleaning: {
    name: 'Data Cleaning', hoursPerLevel: 8,
    objective: 'Handle missing values, duplicates, and wrong data types to prepare data for analysis.',
    resource: { title: 'Kaggle Learn: Data Cleaning', url: 'https://www.kaggle.com/learn/data-cleaning' },
  },
  dataviz: {
    name: 'Data Visualization', hoursPerLevel: 10,
    objective: 'Create clear charts and dashboards that answer a real question.',
    resource: { title: 'Kaggle Learn: Data Visualization', url: 'https://www.kaggle.com/learn/data-visualization' },
  },
  powerbi: {
    name: 'Power BI / Tableau', hoursPerLevel: 12,
    objective: 'Build interactive reports and dashboards using Power BI or Tableau.',
    resource: { title: 'Microsoft Learn: Power BI', url: 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi' },
  },
  storytelling: {
    name: 'Communication & Data Storytelling', hoursPerLevel: 6,
    objective: 'Explain data findings clearly to people who are not technical.',
    resource: { title: 'Storytelling with Data Blog', url: 'https://www.storytellingwithdata.com/blog' },
  },
  mathml: {
    name: 'Math for ML (Linear Algebra, Probability)', hoursPerLevel: 20,
    objective: 'Learn the vectors, matrices, and probability ideas used in machine learning.',
    resource: { title: 'Khan Academy Linear Algebra', url: 'https://www.khanacademy.org/math/linear-algebra' },
  },
  preprocessing: {
    name: 'Data Preprocessing & Feature Engineering', hoursPerLevel: 10,
    objective: 'Scale, encode, and select features so that models can learn better.',
    resource: { title: 'Kaggle Learn: Feature Engineering', url: 'https://www.kaggle.com/learn/feature-engineering' },
  },
  ml: {
    name: 'Machine Learning (Scikit-learn)', hoursPerLevel: 25,
    objective: 'Train and compare models such as linear regression, decision trees, and random forests.',
    resource: { title: 'Kaggle Learn: Intro to Machine Learning', url: 'https://www.kaggle.com/learn/intro-to-machine-learning' },
  },
  evaluation: {
    name: 'Model Evaluation & Tuning', hoursPerLevel: 10,
    objective: 'Measure models using accuracy, precision, recall, and cross-validation, then tune them.',
    resource: { title: 'Scikit-learn: Model Evaluation', url: 'https://scikit-learn.org/stable/modules/model_evaluation.html' },
  },
  deeplearning: {
    name: 'Deep Learning', hoursPerLevel: 25,
    objective: 'Understand how neural networks learn and how to avoid overfitting.',
    resource: { title: 'Kaggle Learn: Intro to Deep Learning', url: 'https://www.kaggle.com/learn/intro-to-deep-learning' },
  },
  tfpytorch: {
    name: 'TensorFlow / PyTorch', hoursPerLevel: 20,
    objective: 'Build and train a simple neural network using TensorFlow or PyTorch.',
    resource: { title: 'PyTorch Tutorials', url: 'https://pytorch.org/tutorials/' },
  },
  deployment: {
    name: 'Model Deployment Basics', hoursPerLevel: 8,
    objective: 'Save a trained model and serve its predictions through a simple API.',
    resource: { title: 'FastAPI Tutorial', url: 'https://fastapi.tiangolo.com/tutorial/' },
  },
};

// ---------- Career skill matrix (from Phase 1) ----------
// target       = target proficiency (1-5)
// priority     = High / Medium / Low
// prerequisite = skill that should be learned first (text only, for display)
// order        = suggested learning order (already respects prerequisites)
// label        = optional career-specific display name
export const careerRequirements = {
  'full-stack': [
    { skillId: 'html',       target: 4, priority: 'High',   prerequisite: null,                  order: 1 },
    { skillId: 'css',        target: 4, priority: 'High',   prerequisite: 'HTML',                order: 2 },
    { skillId: 'javascript', target: 4, priority: 'High',   prerequisite: 'HTML',                order: 3 },
    { skillId: 'git',        target: 3, priority: 'Medium', prerequisite: null,                  order: 4 },
    { skillId: 'react',      target: 4, priority: 'High',   prerequisite: 'JavaScript',          order: 5 },
    { skillId: 'sql',        target: 3, priority: 'High',   prerequisite: null,                  order: 6, label: 'SQL & Databases' },
    { skillId: 'node',       target: 3, priority: 'High',   prerequisite: 'JavaScript',          order: 7 },
    { skillId: 'rest',       target: 4, priority: 'High',   prerequisite: 'Node.js & Express',   order: 8 },
    { skillId: 'auth',       target: 3, priority: 'Medium', prerequisite: 'REST APIs',           order: 9 },
    { skillId: 'testing',    target: 3, priority: 'Low',    prerequisite: 'JavaScript',          order: 10 },
  ],
  'data-analyst': [
    { skillId: 'excel',        target: 4, priority: 'High',   prerequisite: null,                  order: 1 },
    { skillId: 'sql',          target: 4, priority: 'High',   prerequisite: null,                  order: 2 },
    { skillId: 'python',       target: 3, priority: 'High',   prerequisite: null,                  order: 3 },
    { skillId: 'pandas',       target: 4, priority: 'High',   prerequisite: 'Python',              order: 4 },
    { skillId: 'statistics',   target: 3, priority: 'High',   prerequisite: null,                  order: 5 },
    { skillId: 'cleaning',     target: 4, priority: 'Medium', prerequisite: 'Pandas & NumPy',      order: 6 },
    { skillId: 'dataviz',      target: 4, priority: 'High',   prerequisite: 'Pandas & NumPy',      order: 7 },
    { skillId: 'powerbi',      target: 3, priority: 'Medium', prerequisite: 'Excel',               order: 8 },
    { skillId: 'storytelling', target: 3, priority: 'Medium', prerequisite: 'Data Visualization',  order: 9 },
  ],
  'ai-ml': [
    { skillId: 'python',        target: 4, priority: 'High',   prerequisite: null,                                  order: 1 },
    { skillId: 'mathml',        target: 3, priority: 'High',   prerequisite: null,                                  order: 2 },
    { skillId: 'statistics',    target: 3, priority: 'High',   prerequisite: null,                                  order: 3 },
    { skillId: 'pandas',        target: 4, priority: 'High',   prerequisite: 'Python',                              order: 4 },
    { skillId: 'preprocessing', target: 4, priority: 'High',   prerequisite: 'Pandas & NumPy',                      order: 5 },
    { skillId: 'ml',            target: 4, priority: 'High',   prerequisite: 'Math for ML, Pandas & NumPy',         order: 6 },
    { skillId: 'evaluation',    target: 4, priority: 'Medium', prerequisite: 'Machine Learning (Scikit-learn)',     order: 7 },
    { skillId: 'deeplearning',  target: 3, priority: 'High',   prerequisite: 'Machine Learning (Scikit-learn)',     order: 8 },
    { skillId: 'tfpytorch',     target: 3, priority: 'Medium', prerequisite: 'Deep Learning',                       order: 9 },
    { skillId: 'sql',           target: 3, priority: 'Medium', prerequisite: null,                                  order: 10 },
    { skillId: 'git',           target: 3, priority: 'Low',    prerequisite: null,                                  order: 11 },
    { skillId: 'deployment',    target: 2, priority: 'Low',    prerequisite: 'Model Evaluation & Tuning',           order: 12 },
  ],
};

// ---------- Demo student (used by the "Try demo account" button) ----------
export const sampleStudent = {
  name: 'Pravin',
  email: 'pravin@example.com',
  education: 'Undergraduate - Year 2',
  studyHoursPerWeek: 10,
};

export const sampleCareerId = 'full-stack';

// Current proficiency (1-5), keyed by skill id
export const sampleRatings = {
  html: 4, css: 3, javascript: 3, git: 3,
  react: 1, sql: 1, node: 1, rest: 1, auth: 1, testing: 2,
  python: 3,
};

// Which careers the student has already assessed
export const sampleAssessed = { 'full-stack': true };

// Progress on learning activities, keyed by skill id
export const sampleActivityStatus = {
  css: 'Completed',
  javascript: 'In Progress',
};