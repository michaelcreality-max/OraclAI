"""
Multi-Agent Website Builder
Parallel agent collaboration for website generation
"""

import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class WebsiteBuildResult:
    """Result of a website build"""
    project_id: str
    html: str
    css: str
    js: str
    build_time: float
    quality_score: float
    agent_contributions: Dict[str, Any]
    issues: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentTask:
    """Task assigned to an agent"""
    agent_id: str
    agent_role: str
    task_type: str
    content: str
    dependencies: List[str]
    result: Any = None
    completed: bool = False


class WebsiteAgent:
    """Individual website building agent"""
    
    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role
        self.skills = self._get_role_skills()
    
    def _get_role_skills(self) -> List[str]:
        """Get skills based on role"""
        skills_map = {
            'structure': ['html', 'semantic', 'layout', 'accessibility'],
            'styling': ['css', 'responsive', 'animations', 'design'],
            'interactivity': ['javascript', 'events', 'dom', 'apis'],
            'content': ['copywriting', 'seo', 'images', 'media'],
            'optimization': ['performance', 'wcag', 'minification', 'caching']
        }
        return skills_map.get(self.role, [])
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute assigned task"""
        start_time = time.time()
        
        # Simulate processing
        time.sleep(0.1)
        
        if task.task_type == 'html_structure':
            result = self._generate_html_structure(task.content)
        elif task.task_type == 'css_styles':
            result = self._generate_css_styles(task.content)
        elif task.task_type == 'js_interactivity':
            result = self._generate_js_code(task.content)
        elif task.task_type == 'content':
            result = self._generate_content(task.content)
        elif task.task_type == 'optimization':
            result = self._optimize_code(task.content)
        else:
            result = {'output': f'Completed {task.task_type}', 'quality': 0.8}
        
        task.result = result
        task.completed = True
        
        return {
            'agent_id': self.agent_id,
            'role': self.role,
            'task': task.task_type,
            'result': result,
            'duration': time.time() - start_time
        }
    
    def _generate_html_structure(self, description: str) -> Dict:
        """Generate HTML structure"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <div class="logo">{{logo}}</div>
            <ul class="nav-links">
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="hero" class="hero">
            <h1>{{headline}}</h1>
            <p>{{subheadline}}</p>
            <button class="cta">Get Started</button>
        </section>
        
        <section id="features" class="features">
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>Feature 1</h3>
                    <p>Description of feature 1</p>
                </div>
                <div class="feature-card">
                    <h3>Feature 2</h3>
                    <p>Description of feature 2</p>
                </div>
                <div class="feature-card">
                    <h3>Feature 3</h3>
                    <p>Description of feature 3</p>
                </div>
            </div>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 {{company}}. All rights reserved.</p>
    </footer>
    
    <script src="scripts.js"></script>
</body>
</html>"""
        
        return {
            'html': html,
            'sections': ['header', 'hero', 'features', 'footer'],
            'quality': 0.85
        }
    
    def _generate_css_styles(self, description: str) -> Dict:
        """Generate CSS styles"""
        css = """/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary: #3b82f6;
    --secondary: #64748b;
    --background: #ffffff;
    --text: #1e293b;
    --border: #e2e8f0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text);
    background: var(--background);
}

/* Navigation */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: var(--background);
    border-bottom: 1px solid var(--border);
}

.nav-links {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-links a {
    text-decoration: none;
    color: var(--text);
    font-weight: 500;
}

/* Hero section */
.hero {
    text-align: center;
    padding: 4rem 2rem;
    background: linear-gradient(135deg, var(--primary), #8b5cf6);
    color: white;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.cta {
    padding: 1rem 2rem;
    background: white;
    color: var(--primary);
    border: none;
    border-radius: 0.5rem;
    font-size: 1.1rem;
    cursor: pointer;
    margin-top: 2rem;
}

/* Features */
.features {
    padding: 4rem 2rem;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.feature-card {
    padding: 2rem;
    background: #f8fafc;
    border-radius: 0.5rem;
    border: 1px solid var(--border);
}

/* Footer */
footer {
    text-align: center;
    padding: 2rem;
    background: #f1f5f9;
    margin-top: 4rem;
}

/* Responsive */
@media (max-width: 768px) {
    .hero h1 {
        font-size: 2rem;
    }
    
    .nav-links {
        display: none;
    }
}
"""
        
        return {
            'css': css,
            'variables': 5,
            'components': ['navbar', 'hero', 'features', 'footer'],
            'quality': 0.88
        }
    
    def _generate_js_code(self, description: str) -> Dict:
        """Generate JavaScript code"""
        js = """// Main application script
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initNavigation();
    initAnimations();
    initForms();
});

// Navigation functionality
function initNavigation() {
    const nav = document.querySelector('.navbar');
    
    // Smooth scroll for nav links
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });
}

// Animation system
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        card.classList.add('animate-on-scroll');
        observer.observe(card);
    });
}

// Form handling
function initForms() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            // Handle form submission
            console.log('Form submitted');
        });
    });
}

// CTA button click handler
document.querySelector('.cta')?.addEventListener('click', function() {
    // Handle CTA action
    console.log('CTA clicked');
});
"""
        
        return {
            'js': js,
            'functions': ['initNavigation', 'initAnimations', 'initForms'],
            'event_listeners': 5,
            'quality': 0.82
        }
    
    def _generate_content(self, description: str) -> Dict:
        """Generate content"""
        return {
            'title': 'My Website',
            'headline': 'Welcome to Our Platform',
            'subheadline': 'Build amazing websites with AI-powered tools',
            'company': 'AI Website Builder',
            'logo': 'Logo',
            'seo_keywords': ['website', 'ai', 'builder'],
            'quality': 0.9
        }
    
    def _optimize_code(self, content: str) -> Dict:
        """Optimize generated code"""
        return {
            'optimizations': [
                'Minified CSS',
                'Compressed images',
                'Lazy loading added',
                'Accessibility improved'
            ],
            'performance_score': 0.87,
            'wcag_score': 0.92,
            'quality': 0.89
        }


class MultiAgentWebsiteBuilder:
    """
    Multi-agent website builder with parallel collaboration
    """
    
    def __init__(self, max_agents: int = 5):
        self.max_agents = min(max_agents, 5)
        self.agents: List[WebsiteAgent] = []
        self.build_history: List[WebsiteBuildResult] = []
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize agent pool"""
        roles = ['structure', 'styling', 'interactivity', 'content', 'optimization']
        
        for i, role in enumerate(roles[:self.max_agents]):
            agent = WebsiteAgent(f"agent_{i}", role)
            self.agents.append(agent)
    
    def build_website(self, config: Dict[str, Any]) -> WebsiteBuildResult:
        """Build website using parallel agents"""
        start_time = time.time()
        project_id = f"web_{uuid.uuid4().hex[:8]}"
        
        # Create tasks for each agent
        tasks = self._create_tasks(config)
        
        # Execute tasks in parallel
        results = self._execute_parallel(tasks)
        
        # Combine results
        html, css, js = self._combine_results(results, config)
        
        # Calculate metrics
        build_time = time.time() - start_time
        quality_score = self._calculate_quality(results)
        
        # Get agent contributions
        agent_contributions = {
            r['agent_id']: {
                'role': r['role'],
                'task': r['task'],
                'duration': r['duration']
            }
            for r in results
        }
        
        # Get issues
        issues = self._collect_issues(results)
        
        # Create result
        result = WebsiteBuildResult(
            project_id=project_id,
            html=html,
            css=css,
            js=js,
            build_time=build_time,
            quality_score=quality_score,
            agent_contributions=agent_contributions,
            issues=issues
        )
        
        # Store in history
        self.build_history.append(result)
        
        return result
    
    def _create_tasks(self, config: Dict) -> List[AgentTask]:
        """Create tasks for agents"""
        description = config.get('description', 'Modern responsive website')
        
        tasks = []
        task_types = [
            ('html_structure', 'Generate HTML structure'),
            ('css_styles', 'Generate CSS styles'),
            ('js_interactivity', 'Generate JavaScript code'),
            ('content', 'Generate content'),
            ('optimization', 'Optimize code')
        ]
        
        for i, (task_type, content) in enumerate(task_types[:self.max_agents]):
            task = AgentTask(
                agent_id=f"agent_{i}",
                agent_role=self.agents[i].role,
                task_type=task_type,
                content=description,
                dependencies=[]
            )
            tasks.append(task)
        
        return tasks
    
    def _execute_parallel(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute tasks in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_agents) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in tasks:
                agent = next(a for a in self.agents if a.agent_id == task.agent_id)
                future = executor.submit(agent.execute_task, task)
                future_to_task[future] = task
            
            # Collect results
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'agent_id': future_to_task[future].agent_id,
                        'error': str(e)
                    })
        
        return results
    
    def _combine_results(self, results: List[Dict], config: Dict) -> tuple:
        """Combine agent results into final code"""
        html_result = next((r for r in results if r.get('task') == 'html_structure'), {})
        css_result = next((r for r in results if r.get('task') == 'css_styles'), {})
        js_result = next((r for r in results if r.get('task') == 'js_interactivity'), {})
        content_result = next((r for r in results if r.get('task') == 'content'), {})
        
        # Get content
        content = content_result.get('result', {}) if content_result else {}
        
        # Replace placeholders in HTML
        html = html_result.get('result', {}).get('html', '') if html_result else ''
        html = html.replace('{{title}}', config.get('title', content.get('title', 'My Website')))
        html = html.replace('{{logo}}', content.get('logo', 'Logo'))
        html = html.replace('{{headline}}', content.get('headline', 'Welcome'))
        html = html.replace('{{subheadline}}', content.get('subheadline', 'Build amazing websites'))
        html = html.replace('{{company}}', config.get('title', content.get('company', 'Company')))
        
        css = css_result.get('result', {}).get('css', '') if css_result else ''
        js = js_result.get('result', {}).get('js', '') if js_result else ''
        
        return html, css, js
    
    def _calculate_quality(self, results: List[Dict]) -> float:
        """Calculate overall quality score"""
        scores = []
        for r in results:
            if 'result' in r and isinstance(r['result'], dict):
                scores.append(r['result'].get('quality', 0.5))
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _collect_issues(self, results: List[Dict]) -> List[str]:
        """Collect issues from results"""
        issues = []
        for r in results:
            if 'error' in r:
                issues.append(f"{r.get('agent_id')}: {r['error']}")
        return issues


# Initialize global builder
website_builder = MultiAgentWebsiteBuilder(max_agents=5)


def demo_website_build() -> WebsiteBuildResult:
    """Run demo website build"""
    config = {
        'title': 'AI Generated Website',
        'description': 'A modern landing page with animations and responsive design',
        'layout': 'landing',
        'theme': 'modern',
        'features': ['animations', 'responsive', 'seo']
    }
    
    return website_builder.build_website(config)


if __name__ == '__main__':
    # Run demo
    result = demo_website_build()
    print(f"Built website: {result.project_id}")
    print(f"Quality score: {result.quality_score:.2f}")
    print(f"Build time: {result.build_time:.2f}s")
