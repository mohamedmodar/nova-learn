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
  Linkedin
} from 'lucide-react';

const AboutUs = () => {
  const teamMembers = [
    {
      name: "Dr. Sarah Chen",
      role: "Founder & AI Research Lead",
      description: "PhD in Machine Learning with 10+ years in educational technology",
      avatar: "SC",
      skills: ["AI/ML", "EdTech", "Research"]
    },
    {
      name: "Michael Rodriguez",
      role: "Lead Developer",
      description: "Full-stack engineer passionate about creating accessible learning platforms",
      avatar: "MR",
      skills: ["React", "Node.js", "Python"]
    },
    {
      name: "Emily Johnson",
      role: "UX/UI Designer",
      description: "Design expert focused on creating intuitive and engaging user experiences",
      avatar: "EJ",
      skills: ["UI/UX", "Design Systems", "User Research"]
    },
    {
      name: "David Kim",
      role: "Data Scientist",
      description: "Specialist in recommendation systems and learning analytics",
      avatar: "DK",
      skills: ["Data Science", "Analytics", "ML Models"]
    }
  ];

  const features = [
    {
      icon: <Brain className="h-6 w-6" />,
      title: "AI-Powered Recommendations",
      description: "Our advanced machine learning algorithms analyze your learning patterns, preferences, and goals to suggest the most relevant courses for your journey."
    },
    {
      icon: <TrendingUp className="h-6 w-6" />,
      title: "Progress Tracking",
      description: "Monitor your learning progress with detailed analytics, completion rates, and personalized insights to keep you motivated and on track."
    },
    {
      icon: <Globe className="h-6 w-6" />,
      title: "Multi-Platform Integration",
      description: "Access courses from top universities and online platforms like Coursera, Udemy, and edX, all in one unified learning experience."
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: "Personalized Learning Paths",
      description: "Get customized learning trajectories based on your skill level, career goals, and time availability for optimal learning outcomes."
    },
    {
      icon: <Award className="h-6 w-6" />,
      title: "Skill Assessment",
      description: "Regular evaluations and skill assessments help identify knowledge gaps and recommend targeted learning resources."
    },
    {
      icon: <Lightbulb className="h-6 w-6" />,
      title: "Smart Matching",
      description: "Our two-tower neural network model ensures highly accurate course recommendations that match your learning style and objectives."
    }
  ];

  const stats = [
    { value: "50,000+", label: "Active Learners" },
    { value: "10,000+", label: "Courses Available" },
    { value: "95%", label: "Satisfaction Rate" },
    { value: "500+", label: "Partner Institutions" }
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
              Revolutionizing education through AI-powered personalized learning recommendations
            </p>
            <p className="text-lg text-blue-200 max-w-3xl mx-auto">
              We believe that everyone deserves access to quality education tailored to their unique learning style, 
              goals, and pace. Our platform combines cutting-edge AI technology with comprehensive course catalogs 
              to create the ultimate personalized learning experience.
            </p>
          </div>
        </div>

        {/* Mission & Vision */}
        <div className="grid md:grid-cols-2 gap-8">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Target className="h-6 w-6 text-blue-600" />
                <CardTitle>Our Mission</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                To democratize quality education by leveraging artificial intelligence to provide personalized, 
                accessible, and effective learning experiences for learners worldwide. We strive to bridge the 
                gap between individual learning needs and available educational resources.
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-indigo-500">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Heart className="h-6 w-6 text-indigo-600" />
                <CardTitle>Our Vision</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                To create a world where learning is truly personalized, where every individual can discover 
                and pursue their educational goals with confidence, supported by intelligent technology that 
                understands and adapts to their unique learning journey.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Statistics */}
        <div className="bg-gray-50 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-center mb-8">Our Impact</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">{stat.value}</div>
                <div className="text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Features */}
        <div>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">What Makes Us Different</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Our platform combines advanced AI technology with educational expertise to deliver 
              unparalleled personalized learning experiences.
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
          <h2 className="text-2xl font-bold text-center mb-8">Powered by Advanced Technology</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Machine Learning</h3>
              <p className="text-gray-600">
                Two-tower neural networks and collaborative filtering for accurate recommendations
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="h-8 w-8 text-indigo-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Natural Language Processing</h3>
              <p className="text-gray-600">
                SBERT embeddings for semantic course matching and content analysis
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Real-time Analytics</h3>
              <p className="text-gray-600">
                Advanced learning analytics and performance tracking for continuous improvement
              </p>
            </div>
          </div>
        </div>

        {/* Team Section */}
        <div>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Meet Our Team</h2>
            <p className="text-lg text-gray-600">
              Passionate educators, technologists, and researchers dedicated to transforming learning
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {teamMembers.map((member, index) => (
              <Card key={index} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl font-bold text-white">{member.avatar}</span>
                  </div>
                  <CardTitle className="text-lg">{member.name}</CardTitle>
                  <CardDescription className="font-medium text-blue-600">
                    {member.role}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">{member.description}</p>
                  <div className="flex flex-wrap gap-1 justify-center">
                    {member.skills.map((skill) => (
                      <Badge key={skill} variant="outline" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Contact Section */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Get in Touch</h2>
            <p className="text-gray-600 mb-6">
              Have questions about NovaLearn or want to partner with us? We'd love to hear from you!
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Mail className="h-4 w-4 mr-2" />
                Contact Us
              </Button>
              <Button variant="outline">
                <Github className="h-4 w-4 mr-2" />
                View on GitHub
              </Button>
              <Button variant="outline">
                <Linkedin className="h-4 w-4 mr-2" />
                Follow Us
              </Button>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to Transform Your Learning?</h2>
          <p className="text-blue-100 mb-6">
            Join thousands of learners who have already discovered their perfect educational path with NovaLearn
          </p>
          <Button 
            size="lg" 
            className="bg-white text-blue-600 hover:bg-gray-100"
            onClick={() => window.location.href = '/home'}
          >
            Start Learning Today
          </Button>
        </div>
      </div>
    </Layout>
  );
};

export default AboutUs; 