import React from 'react';
import Layout from '../components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  GraduationCap, 
  Target, 
  Users, 
  BookOpen, 
  Brain, 
  TrendingUp,
  Award,
  Globe,
  Lightbulb,
  Heart,
  Mail,
  Github,
  Linkedin,
  Code,
  Database,
  Cpu
} from 'lucide-react';

const AboutUs = () => {
  const features = [
    {
      icon: <Brain className="h-6 w-6" />,
      title: "Hybrid Recommendation System",
      description: "Our advanced hybrid model combines collaborative filtering, content-based filtering, and deep learning approaches using a two-tower neural network architecture for highly accurate course recommendations."
    },
    {
      icon: <TrendingUp className="h-6 w-6" />,
      title: "Real-time Learning Analytics",
      description: "Track your learning progress with comprehensive analytics including course completion rates, learning patterns, and personalized insights to optimize your educational journey."
    },
    {
      icon: <Globe className="h-6 w-6" />,
      title: "Multi-Source Course Integration",
      description: "Access courses from multiple educational platforms including Coursera, edX, and other major online learning providers, all aggregated in one unified platform."
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: "Personalized Learning Paths",
      description: "Get customized learning trajectories based on your skill assessment, learning goals, time availability, and preferred learning formats for optimal outcomes."
    },
    {
      icon: <Award className="h-6 w-6" />,
      title: "Skill-Based Matching",
      description: "Our system analyzes course content and matches it with your current skills and desired learning objectives using advanced NLP techniques and SBERT embeddings."
    },
    {
      icon: <Lightbulb className="h-6 w-6" />,
      title: "AI-Powered Chatbot",
      description: "Interact with Nova, our intelligent assistant powered by Google's Gemini AI, to get instant course recommendations and answers to your learning questions."
    }
  ];

  const techStack = [
    {
      icon: <Code className="h-8 w-8" />,
      title: "Frontend Technologies",
      technologies: ["React.js", "TypeScript", "Tailwind CSS", "Vite", "shadcn/ui"],
      color: "blue"
    },
    {
      icon: <Database className="h-8 w-8" />,
      title: "Backend Technologies", 
      technologies: ["FastAPI", "Python", "PostgreSQL", "SQLAlchemy", "Pydantic"],
      color: "green"
    },
    {
      icon: <Cpu className="h-8 w-8" />,
      title: "AI/ML Technologies",
      technologies: ["TensorFlow", "Scikit-learn", "SBERT", "Pandas", "NumPy", "Google Gemini API"],
      color: "purple"
    }
  ];

  return (
    <Layout>
      <div className="space-y-12">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-8 text-white">
          <div className="max-w-4xl mx-auto text-center">
            <div className="flex items-center justify-center space-x-3 mb-6">
              <GraduationCap className="h-12 w-12" />
              <h1 className="text-4xl font-bold">NovaLearn</h1>
            </div>
            <p className="text-xl text-blue-100 mb-6">
              An AI-Powered Learning Platform Recommender System
            </p>
            <p className="text-lg text-blue-200 max-w-3xl mx-auto">
              A comprehensive graduation project that combines machine learning, natural language processing, 
              and modern web technologies to create an intelligent learning platform that provides personalized 
              course recommendations tailored to individual learning goals and preferences.
            </p>
          </div>
        </div>

        {/* Project Overview */}
        <div className="grid md:grid-cols-2 gap-8">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Target className="h-6 w-6 text-blue-600" />
                <CardTitle>Project Objective</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                To develop an intelligent learning platform that leverages artificial intelligence and machine learning 
                to provide personalized course recommendations, helping learners discover the most suitable educational 
                content based on their skills, goals, and learning preferences.
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-indigo-500">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Brain className="h-6 w-6 text-indigo-600" />
                <CardTitle>Technical Innovation</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Our system implements a hybrid recommendation approach combining collaborative filtering, 
                content-based filtering, and deep learning using a two-tower neural network architecture. 
                The platform integrates SBERT for semantic course matching and Google's Gemini AI for conversational assistance.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Key Features */}
        <div>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Platform Features</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Our platform combines cutting-edge AI technology with practical educational tools 
              to deliver a comprehensive personalized learning experience.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                      {feature.icon}
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Technology Stack */}
        <div className="bg-white border rounded-lg p-8">
          <h2 className="text-2xl font-bold text-center mb-8">Technology Stack</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {techStack.map((stack, index) => (
              <div key={index} className="text-center">
                <div className={`w-16 h-16 bg-${stack.color}-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <div className={`text-${stack.color}-600`}>
                    {stack.icon}
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-3">{stack.title}</h3>
                <div className="flex flex-wrap justify-center gap-2">
                  {stack.technologies.map((tech, techIndex) => (
                    <Badge key={techIndex} variant="secondary" className="text-xs">
                      {tech}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ML Model Architecture */}
        <div className="bg-gray-50 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-center mb-8">Machine Learning Architecture</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Two-Tower Neural Network
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Our core recommendation engine uses a two-tower architecture that separately encodes 
                  user preferences and course features, enabling efficient similarity computation and scalable recommendations.
                </p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  <li>User tower: Encodes user profiles and interaction history</li>
                  <li>Item tower: Encodes course features and content</li>
                  <li>Dense layers with dropout for regularization</li>
                  <li>Cosine similarity for recommendation scoring</li>
                </ul>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Semantic Matching
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  We leverage SBERT (Sentence-BERT) embeddings for semantic understanding of course 
                  content and user queries, enabling more accurate content-based recommendations.
                </p>
                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                  <li>Course description vectorization</li>
                  <li>Skill and topic extraction</li>
                  <li>Query-course semantic similarity</li>
                  <li>Multi-language support capability</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Graduation Project Team */}
        <div>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Graduation Project Team</h2>
          
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[
              { name: "Anas Ahmed", id: "2018170104", role: "Team Leader"  },
              { name: "Mostafa Maher", id: "2017170439" },
              { name: "Ahmed Ali", id: "2015170027" },
              { name: "Ahmed Ashraf", id: "2018170016" }
            ].map((member, index) => (
              <Card key={index} className="text-center p-6 hover:shadow-lg transition-shadow">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-lg">
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <CardTitle className="text-lg mb-1">{member.name}</CardTitle>
                <CardDescription className="text-sm text-gray-500 mb-2">{member.id}</CardDescription>
                <Badge variant="outline" className="text-xs">{member.role}</Badge>
              </Card>
            ))}
          </div>

          <div className="text-center bg-blue-50 rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4">Project Supervision</h3>
            <div className="flex flex-col md:flex-row justify-center items-center gap-8">
              <Card className="p-4">
                <CardTitle className="text-lg">Dr. Ahmed Ezzat</CardTitle>
                <CardDescription>Project Supervisor</CardDescription>
              </Card>
              <Card className="p-4">
                <CardTitle className="text-lg">TA. Ahmed Tohamy</CardTitle>
                <CardDescription>Teaching Assistant</CardDescription>
              </Card>
            </div>
          </div>
        </div>

        {/* Project Scope & Impact */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="text-center p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Database className="h-6 w-6 text-blue-600" />
            </div>
            <CardTitle className="text-lg mb-2">Course Database</CardTitle>
            <p className="text-2xl font-bold text-blue-600 mb-2">10,000+</p>
            <CardDescription>Courses from multiple platforms aggregated and processed</CardDescription>
          </Card>
          
          <Card className="text-center p-6">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Brain className="h-6 w-6 text-green-600" />
            </div>
            <CardTitle className="text-lg mb-2">ML Model Accuracy</CardTitle>
            <p className="text-2xl font-bold text-green-600 mb-2">85%+</p>
            <CardDescription>Recommendation accuracy based on evaluation metrics</CardDescription>
          </Card>
          
          <Card className="text-center p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Code className="h-6 w-6 text-purple-600" />
            </div>
            <CardTitle className="text-lg mb-2">Lines of Code</CardTitle>
            <p className="text-2xl font-bold text-purple-600 mb-2">15,000+</p>
            <CardDescription>Full-stack implementation with ML models</CardDescription>
          </Card>
        </div>

        {/* Repository & Documentation */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Project Resources</h2>
            <p className="text-gray-600 mb-6">
              Explore our codebase, documentation, and research findings for this graduation project.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Github className="h-4 w-4 mr-2" />
                View Source Code
              </Button>
              <Button variant="outline">
                <BookOpen className="h-4 w-4 mr-2" />
                Project Documentation
              </Button>
              <Button variant="outline">
                <Award className="h-4 w-4 mr-2" />
                Research Paper
              </Button>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <Card className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-center p-8">
          <CardHeader>
            <CardTitle className="text-3xl font-bold">Experience AI-Powered Learning</CardTitle>
            <CardDescription className="text-blue-100 text-lg mt-2">
              Try our intelligent recommendation system and discover personalized learning paths.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button size="lg" variant="secondary" onClick={() => window.location.href = '/register'}>
              Start Learning with NovaLearn
              <Brain className="h-5 w-5 ml-2" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default AboutUs; 