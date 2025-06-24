
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ArrowLeft, 
  Star, 
  Clock, 
  Users, 
  BookOpen, 
  Play,
  ExternalLink,
  Heart,
  Share
} from 'lucide-react';

interface CourseDetail {
  id: string;
  title: string;
  description: string;
  longDescription: string;
  provider: string;
  instructor: string;
  level: string;
  rating: number;
  adjustedRating: number;
  reviewCount: number;
  duration: string;
  enrollmentCount: number;
  skills: string[];
  progress?: number;
  isExternal?: boolean;
  syllabus: string[];
  requirements: string[];
}

const CourseDetails = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEnrolled, setIsEnrolled] = useState(false);

  useEffect(() => {
    const fetchCourseDetails = async () => {
      // Mock API call
      const mockCourse: CourseDetail = {
        id: id || '1',
        title: 'Complete React Developer Course',
        description: 'Build modern web applications with React, Redux, and more',
        longDescription: 'This comprehensive course will teach you everything you need to know about React development. From basic components to advanced state management with Redux, you\'ll build real-world projects and gain the skills needed for modern web development.',
        provider: 'Udemy',
        instructor: 'John Smith',
        level: 'Intermediate',
        rating: 4.6,
        adjustedRating: 4.8,
        reviewCount: 12543,
        duration: '40 hours',
        enrollmentCount: 45230,
        skills: ['React', 'JavaScript', 'Redux', 'Web Development', 'Node.js', 'MongoDB'],
        progress: id === '1' ? 65 : undefined,
        isExternal: id !== '1' && id !== '2',
        syllabus: [
          'Introduction to React',
          'Components and JSX',
          'State and Props',
          'Event Handling',
          'React Hooks',
          'Context API',
          'Redux Fundamentals',
          'Async Actions with Redux',
          'React Router',
          'Building Real Projects'
        ],
        requirements: [
          'Basic JavaScript knowledge',
          'Understanding of HTML and CSS',
          'Familiarity with ES6+ features',
          'Node.js installed on your machine'
        ]
      };

      setCourse(mockCourse);
      setIsEnrolled(!!mockCourse.progress);
      setLoading(false);
    };

    fetchCourseDetails();
  }, [id]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (!course) {
    return (
      <Layout>
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Course not found</h1>
          <Button onClick={() => navigate('/home')}>Back to Home</Button>
        </div>
      </Layout>
    );
  }

  const handleEnroll = () => {
    setIsEnrolled(true);
    console.log('Enrolled in course:', course.id);
  };

  const handleContinue = () => {
    console.log('Continue course:', course.id);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <Button 
          variant="ghost" 
          onClick={() => navigate(-1)}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <CardTitle className="text-2xl">{course.title}</CardTitle>
                    <CardDescription className="text-lg">{course.description}</CardDescription>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>By {course.instructor}</span>
                      <Badge variant="secondary">{course.provider}</Badge>
                      <Badge>{course.level}</Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Heart className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Share className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-6 mb-4">
                  <div className="flex items-center gap-1">
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                    <span className="font-medium">{course.adjustedRating}</span>
                    <span className="text-gray-600">({course.reviewCount.toLocaleString()} reviews)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="h-5 w-5 text-gray-400" />
                    <span className="text-gray-600">{course.enrollmentCount.toLocaleString()} students</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-5 w-5 text-gray-400" />
                    <span className="text-gray-600">{course.duration}</span>
                  </div>
                </div>

                {course.progress !== undefined && (
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span>Your Progress</span>
                      <span>{course.progress}%</span>
                    </div>
                    <Progress value={course.progress} className="w-full" />
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  {course.skills.map((skill) => (
                    <Badge key={skill} variant="outline">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Tabs defaultValue="overview" className="w-full">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="syllabus">Syllabus</TabsTrigger>
                <TabsTrigger value="requirements">Requirements</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>About this course</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700 leading-relaxed">{course.longDescription}</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="syllabus" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Course Content</CardTitle>
                    <CardDescription>{course.syllabus.length} modules</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {course.syllabus.map((module, index) => (
                        <div key={index} className="flex items-center gap-3 p-3 rounded-lg border">
                          <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full text-blue-600 font-medium text-sm">
                            {index + 1}
                          </div>
                          <span className="font-medium">{module}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="requirements" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Prerequisites</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {course.requirements.map((requirement, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                          <span>{requirement}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          <div className="space-y-6">
            <Card>
              <CardContent className="pt-6">
                {isEnrolled ? (
                  <div className="space-y-4">
                    <Button 
                      className="w-full" 
                      onClick={handleContinue}
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Continue Learning
                    </Button>
                    <div className="text-center text-sm text-gray-600">
                      You're enrolled in this course
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Button 
                      className="w-full bg-green-600 hover:bg-green-700" 
                      onClick={handleEnroll}
                    >
                      {course.isExternal ? (
                        <>
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Enroll Now
                        </>
                      ) : (
                        <>
                          <BookOpen className="h-4 w-4 mr-2" />
                          Start Course
                        </>
                      )}
                    </Button>
                    {course.isExternal && (
                      <div className="text-center text-sm text-gray-600">
                        Redirects to {course.provider}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Course Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Level:</span>
                  <Badge>{course.level}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span>{course.duration}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Provider:</span>
                  <span>{course.provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Instructor:</span>
                  <span>{course.instructor}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default CourseDetails;
