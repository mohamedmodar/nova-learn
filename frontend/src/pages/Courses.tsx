import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { BookOpen, Clock, Star, ExternalLink, Search, Users, GraduationCap } from 'lucide-react';

interface Course {
  id: string;
  title: string;
  description: string;
  provider: string;
  level: string;
  rating: number;
  adjustedRating: number;
  duration: string;
  skills: string[];
  progress?: number;
  isExternal?: boolean;
  enrolled?: number;
  category: string;
}

const Courses = () => {
  const navigate = useNavigate();
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [filteredCourses, setFilteredCourses] = useState<Course[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAllCourses = async () => {
      // Mock comprehensive course data
      const mockCourses: Course[] = [
        // Internal University Courses
        {
          id: '1',
          title: 'Introduction to Computer Science',
          description: 'Fundamental concepts of programming and computer science with hands-on coding exercises',
          provider: 'University',
          level: 'Beginner',
          rating: 4.5,
          adjustedRating: 4.5,
          duration: '12 weeks',
          skills: ['Programming', 'Algorithms', 'Data Structures', 'Python'],
          progress: 65,
          enrolled: 245,
          category: 'Computer Science'
        },
        {
          id: '2',
          title: 'Database Management Systems',
          description: 'Comprehensive course on SQL, database design principles, and modern database technologies',
          provider: 'University',
          level: 'Intermediate',
          rating: 4.2,
          adjustedRating: 4.2,
          duration: '10 weeks',
          skills: ['SQL', 'Database Design', 'Data Modeling', 'PostgreSQL'],
          progress: 30,
          enrolled: 189,
          category: 'Database'
        },
        {
          id: '3',
          title: 'Advanced Mathematics for CS',
          description: 'Linear algebra, discrete mathematics, and statistical concepts for computer science',
          provider: 'University',
          level: 'Advanced',
          rating: 4.0,
          adjustedRating: 4.0,
          duration: '14 weeks',
          skills: ['Linear Algebra', 'Statistics', 'Discrete Math', 'Calculus'],
          progress: 0,
          enrolled: 156,
          category: 'Mathematics'
        },
        // External Courses
        {
          id: '4',
          title: 'Complete React Developer Course',
          description: 'Build modern web applications with React, Redux, TypeScript and best practices',
          provider: 'Udemy',
          level: 'Intermediate',
          rating: 4.6,
          adjustedRating: 4.8,
          duration: '40 hours',
          skills: ['React', 'JavaScript', 'Redux', 'TypeScript', 'Web Development'],
          isExternal: true,
          enrolled: 89432,
          category: 'Web Development'
        },
        {
          id: '5',
          title: 'Python for Data Science',
          description: 'Master Python programming for data analysis, visualization, and machine learning',
          provider: 'Coursera',
          level: 'Beginner',
          rating: 4.4,
          adjustedRating: 4.6,
          duration: '6 weeks',
          skills: ['Python', 'Data Analysis', 'Pandas', 'NumPy', 'Matplotlib'],
          isExternal: true,
          enrolled: 67543,
          category: 'Data Science'
        },
        {
          id: '6',
          title: 'Machine Learning A-Z',
          description: 'Comprehensive hands-on machine learning course with practical projects',
          provider: 'Udemy',
          level: 'Advanced',
          rating: 4.5,
          adjustedRating: 4.7,
          duration: '44 hours',
          skills: ['Machine Learning', 'Python', 'TensorFlow', 'Statistics', 'AI'],
          isExternal: true,
          enrolled: 125678,
          category: 'AI/ML'
        },
        {
          id: '7',
          title: 'Full Stack Web Development',
          description: 'Complete full-stack development with MERN stack and deployment strategies',
          provider: 'edX',
          level: 'Intermediate',
          rating: 4.3,
          adjustedRating: 4.5,
          duration: '16 weeks',
          skills: ['MongoDB', 'Express', 'React', 'Node.js', 'JavaScript'],
          isExternal: true,
          enrolled: 34567,
          category: 'Web Development'
        },
        {
          id: '8',
          title: 'Cybersecurity Fundamentals',
          description: 'Essential cybersecurity concepts, network security, and ethical hacking basics',
          provider: 'Coursera',
          level: 'Beginner',
          rating: 4.1,
          adjustedRating: 4.3,
          duration: '8 weeks',
          skills: ['Network Security', 'Ethical Hacking', 'Cryptography', 'Risk Assessment'],
          isExternal: true,
          enrolled: 23456,
          category: 'Cybersecurity'
        }
      ];

      setAllCourses(mockCourses);
      setFilteredCourses(mockCourses);
      setLoading(false);
    };

    fetchAllCourses();
  }, []);

  useEffect(() => {
    let filtered = allCourses;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(course =>
        course.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        course.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        course.skills.some(skill => skill.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Filter by level
    if (selectedLevel !== 'all') {
      filtered = filtered.filter(course => course.level === selectedLevel);
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(course => course.category === selectedCategory);
    }

    setFilteredCourses(filtered);
  }, [searchTerm, selectedLevel, selectedCategory, allCourses]);

  const handleCourseClick = (courseId: string) => {
    navigate(`/course/${courseId}`);
  };

  const internalCourses = filteredCourses.filter(course => !course.isExternal);
  const externalCourses = filteredCourses.filter(course => course.isExternal);

  const categories = ['all', ...Array.from(new Set(allCourses.map(course => course.category)))];
  const levels = ['all', 'Beginner', 'Intermediate', 'Advanced'];

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-6 text-white">
          <div className="flex items-center space-x-3 mb-4">
            <BookOpen className="h-8 w-8" />
            <h1 className="text-3xl font-bold">All Courses</h1>
          </div>
          <p className="text-blue-100">Explore our comprehensive catalog of courses tailored for your learning journey</p>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{allCourses.length}</div>
              <div className="text-blue-200">Total Courses</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{internalCourses.length}</div>
              <div className="text-blue-200">University Courses</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{externalCourses.length}</div>
              <div className="text-blue-200">External Recommendations</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search courses..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={selectedLevel} onValueChange={setSelectedLevel}>
              <SelectTrigger>
                <SelectValue placeholder="All Levels" />
              </SelectTrigger>
              <SelectContent>
                {levels.map(level => (
                  <SelectItem key={level} value={level}>
                    {level === 'all' ? 'All Levels' : level}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                {categories.map(category => (
                  <SelectItem key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => {
                setSearchTerm('');
                setSelectedLevel('all');
                setSelectedCategory('all');
              }}
            >
              Clear Filters
            </Button>
          </div>
        </div>

        {/* Courses Tabs */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="all">All Courses ({filteredCourses.length})</TabsTrigger>
            <TabsTrigger value="internal">University ({internalCourses.length})</TabsTrigger>
            <TabsTrigger value="external">External ({externalCourses.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredCourses.map((course) => (
                <CourseCard key={course.id} course={course} onCourseClick={handleCourseClick} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="internal" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {internalCourses.map((course) => (
                <CourseCard key={course.id} course={course} onCourseClick={handleCourseClick} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="external" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {externalCourses.map((course) => (
                <CourseCard key={course.id} course={course} onCourseClick={handleCourseClick} />
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {filteredCourses.length === 0 && (
          <div className="text-center py-12">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No courses found</h3>
            <p className="text-gray-500">Try adjusting your filters or search terms</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

const CourseCard: React.FC<{ course: Course; onCourseClick: (id: string) => void }> = ({ course, onCourseClick }) => {
  return (
    <Card className="hover:shadow-lg transition-all duration-200 cursor-pointer group">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              {course.isExternal ? (
                <ExternalLink className="h-4 w-4 text-green-600" />
              ) : (
                <GraduationCap className="h-4 w-4 text-blue-600" />
              )}
              <Badge variant={course.isExternal ? "default" : "secondary"}>
                {course.provider}
              </Badge>
            </div>
            <CardTitle className="text-lg group-hover:text-blue-600 transition-colors">
              {course.title}
            </CardTitle>
            <CardDescription className="line-clamp-2 mt-1">
              {course.description}
            </CardDescription>
          </div>
          <Badge variant="outline" className="ml-2">
            {course.level}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Skills */}
          <div className="flex flex-wrap gap-1">
            {course.skills.slice(0, 3).map((skill) => (
              <Badge key={skill} variant="outline" className="text-xs">
                {skill}
              </Badge>
            ))}
            {course.skills.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{course.skills.length - 3} more
              </Badge>
            )}
          </div>

          {/* Progress for internal courses */}
          {course.progress !== undefined && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{course.progress}%</span>
              </div>
              <Progress value={course.progress} className="w-full" />
            </div>
          )}

          {/* Course Info */}
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {course.duration}
              </div>
              <div className="flex items-center gap-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                {course.isExternal ? course.adjustedRating : course.rating}
              </div>
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                {course.enrolled?.toLocaleString()}
              </div>
            </div>
          </div>

          {/* Action Button */}
          <Button
            onClick={() => onCourseClick(course.id)}
            className={`w-full ${
              course.isExternal
                ? 'bg-green-600 hover:bg-green-700'
                : course.progress
                ? 'bg-blue-600 hover:bg-blue-700'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {course.isExternal ? (
              <>
                <ExternalLink className="h-4 w-4 mr-2" />
                View Details
              </>
            ) : course.progress ? (
              'Continue Learning'
            ) : (
              'Start Course'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default Courses; 