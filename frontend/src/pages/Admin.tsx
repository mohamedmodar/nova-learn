
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Users, 
  BookOpen, 
  BarChart3,
  Save,
  Eye
} from 'lucide-react';

interface Course {
  id: string;
  title: string;
  description: string;
  provider: string;
  level: string;
  skills: string[];
  isActive: boolean;
}

interface User {
  id: string;
  name: string;
  email: string;
  isStudent: boolean;
  enrolledCourses: number;
  lastActive: string;
}

const Admin = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [courses, setCourses] = useState<Course[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [showAddCourse, setShowAddCourse] = useState(false);

  const [newCourse, setNewCourse] = useState({
    title: '',
    description: '',
    provider: 'University',
    level: 'Beginner',
    skills: ''
  });

  useEffect(() => {
    if (!user?.isAdmin) {
      navigate('/home');
      return;
    }

    // Mock data
    const mockCourses: Course[] = [
      {
        id: '1',
        title: 'Introduction to Computer Science',
        description: 'Fundamental concepts of programming and computer science',
        provider: 'University',
        level: 'Beginner',
        skills: ['Programming', 'Algorithms', 'Data Structures'],
        isActive: true
      },
      {
        id: '2',
        title: 'Database Management Systems',
        description: 'Learn SQL and database design principles',
        provider: 'University',
        level: 'Intermediate',
        skills: ['SQL', 'Database Design', 'Data Modeling'],
        isActive: true
      }
    ];

    const mockUsers: User[] = [
      {
        id: '1',
        name: 'John Doe',
        email: 'john@university.edu',
        isStudent: true,
        enrolledCourses: 3,
        lastActive: '2024-06-21'
      },
      {
        id: '2',
        name: 'Jane Smith',
        email: 'jane@email.com',
        isStudent: false,
        enrolledCourses: 1,
        lastActive: '2024-06-20'
      }
    ];

    setCourses(mockCourses);
    setUsers(mockUsers);
    setLoading(false);
  }, [user, navigate]);

  const handleAddCourse = async () => {
    if (!newCourse.title || !newCourse.description) {
      toast({
        title: "Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    const course: Course = {
      id: Date.now().toString(),
      title: newCourse.title,
      description: newCourse.description,
      provider: newCourse.provider,
      level: newCourse.level,
      skills: newCourse.skills.split(',').map(s => s.trim()).filter(s => s),
      isActive: true
    };

    setCourses([...courses, course]);
    setNewCourse({
      title: '',
      description: '',
      provider: 'University',
      level: 'Beginner',
      skills: ''
    });
    setShowAddCourse(false);

    toast({
      title: "Course added",
      description: "New course has been successfully added.",
    });
  };

  const handleEditCourse = (course: Course) => {
    setEditingCourse(course);
  };

  const handleSaveCourse = async () => {
    if (!editingCourse) return;

    setCourses(courses.map(c => c.id === editingCourse.id ? editingCourse : c));
    setEditingCourse(null);

    toast({
      title: "Course updated",
      description: "Course has been successfully updated.",
    });
  };

  const handleDeleteCourse = (courseId: string) => {
    setCourses(courses.filter(c => c.id !== courseId));
    toast({
      title: "Course deleted",
      description: "Course has been successfully deleted.",
    });
  };

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
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">Manage courses, users, and system analytics</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <BookOpen className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{courses.length}</p>
                  <p className="text-sm text-gray-600">Total Courses</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{users.length}</p>
                  <p className="text-sm text-gray-600">Active Users</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">
                    {users.reduce((acc, u) => acc + u.enrolledCourses, 0)}
                  </p>
                  <p className="text-sm text-gray-600">Total Enrollments</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="courses" className="w-full">
          <TabsList>
            <TabsTrigger value="courses">Course Management</TabsTrigger>
            <TabsTrigger value="users">User Management</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="courses" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Course Management</h2>
              <Button onClick={() => setShowAddCourse(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Course
              </Button>
            </div>

            {showAddCourse && (
              <Card>
                <CardHeader>
                  <CardTitle>Add New Course</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="title">Course Title</Label>
                      <Input
                        id="title"
                        value={newCourse.title}
                        onChange={(e) => setNewCourse({ ...newCourse, title: e.target.value })}
                        placeholder="Enter course title"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="provider">Provider</Label>
                      <Select 
                        value={newCourse.provider} 
                        onValueChange={(value) => setNewCourse({ ...newCourse, provider: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="University">University</SelectItem>
                          <SelectItem value="External">External</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={newCourse.description}
                      onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
                      placeholder="Enter course description"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="level">Level</Label>
                      <Select 
                        value={newCourse.level} 
                        onValueChange={(value) => setNewCourse({ ...newCourse, level: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Beginner">Beginner</SelectItem>
                          <SelectItem value="Intermediate">Intermediate</SelectItem>
                          <SelectItem value="Advanced">Advanced</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="skills">Skills (comma-separated)</Label>
                      <Input
                        id="skills"
                        value={newCourse.skills}
                        onChange={(e) => setNewCourse({ ...newCourse, skills: e.target.value })}
                        placeholder="Python, JavaScript, React"
                      />
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Button onClick={handleAddCourse}>
                      <Save className="h-4 w-4 mr-2" />
                      Add Course
                    </Button>
                    <Button variant="outline" onClick={() => setShowAddCourse(false)}>
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="space-y-4">
              {courses.map((course) => (
                <Card key={course.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg">{course.title}</CardTitle>
                        <CardDescription className="mt-1">{course.description}</CardDescription>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="secondary">{course.provider}</Badge>
                          <Badge>{course.level}</Badge>
                          <Badge variant={course.isActive ? "default" : "secondary"}>
                            {course.isActive ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleEditCourse(course)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => navigate(`/course/${course.id}`)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleDeleteCourse(course.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1">
                      {course.skills.map((skill) => (
                        <Badge key={skill} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {editingCourse && (
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle>Edit Course</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="edit-title">Course Title</Label>
                      <Input
                        id="edit-title"
                        value={editingCourse.title}
                        onChange={(e) => setEditingCourse({ ...editingCourse, title: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-level">Level</Label>
                      <Select 
                        value={editingCourse.level} 
                        onValueChange={(value) => setEditingCourse({ ...editingCourse, level: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Beginner">Beginner</SelectItem>
                          <SelectItem value="Intermediate">Intermediate</SelectItem>
                          <SelectItem value="Advanced">Advanced</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-description">Description</Label>
                    <Textarea
                      id="edit-description"
                      value={editingCourse.description}
                      onChange={(e) => setEditingCourse({ ...editingCourse, description: e.target.value })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="edit-skills">Skills (comma-separated)</Label>
                    <Input
                      id="edit-skills"
                      value={editingCourse.skills.join(', ')}
                      onChange={(e) => setEditingCourse({ 
                        ...editingCourse, 
                        skills: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                      })}
                    />
                  </div>

                  <div className="flex gap-3">
                    <Button onClick={handleSaveCourse}>
                      <Save className="h-4 w-4 mr-2" />
                      Save Changes
                    </Button>
                    <Button variant="outline" onClick={() => setEditingCourse(null)}>
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="users" className="space-y-6">
            <h2 className="text-xl font-semibold">User Management</h2>
            
            <div className="space-y-4">
              {users.map((user) => (
                <Card key={user.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">{user.name}</h3>
                        <p className="text-sm text-gray-600">{user.email}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant={user.isStudent ? "default" : "secondary"}>
                            {user.isStudent ? 'Student' : 'External'}
                          </Badge>
                          <span className="text-sm text-gray-600">
                            {user.enrolledCourses} courses • Last active: {new Date(user.lastActive).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-2" />
                        View Profile
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <h2 className="text-xl font-semibold">Analytics & Insights</h2>
            
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Platform Statistics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Student vs External Users</p>
                      <div className="mt-2">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Students: {users.filter(u => u.isStudent).length}</span>
                          <span>External: {users.filter(u => !u.isStudent).length}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${(users.filter(u => u.isStudent).length / users.length) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-600">Course Distribution</p>
                      <div className="mt-2">
                        <div className="flex justify-between text-sm mb-1">
                          <span>University: {courses.filter(c => c.provider === 'University').length}</span>
                          <span>External: {courses.filter(c => c.provider !== 'University').length}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ width: `${(courses.filter(c => c.provider === 'University').length / courses.length) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recommendation Logs</CardTitle>
                  <CardDescription>Recent system activity and user interactions</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm text-gray-600">
                      <p>• User john@university.edu viewed "Complete React Developer Course"</p>
                      <p>• 5 new course recommendations generated for jane@email.com</p>
                      <p>• Machine learning model updated with 127 new interaction data points</p>
                      <p>• User enrollment increased by 12% this week</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default Admin;
