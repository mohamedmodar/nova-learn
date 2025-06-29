import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { 
  User, 
  Settings, 
  RefreshCw, 
  Save,
  Eye,
  Heart,
  BookOpen 
} from 'lucide-react';

const Profile = () => {
  const { user, updateUser, fetchAndSetUser } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || ''
  });

  // Use useEffect to update form when user object changes
  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
      });
    }
  }, [user]);

  // Mock data for user's activity
  const [favorites] = useState([
    { id: '3', title: 'Complete React Developer Course', provider: 'Udemy' },
    { id: '4', title: 'Python for Data Science', provider: 'Coursera' },
  ]);

  const [recentlyViewed] = useState([
    { id: '5', title: 'Machine Learning A-Z', provider: 'Udemy', viewedAt: '2024-06-21' },
    { id: '6', title: 'Full Stack Web Development', provider: 'University', viewedAt: '2024-06-20' },
  ]);

  // Mock onboarding data
  const [onboarding] = useState({
    learningConfidence: 4,
    coursePreference: ['External Online Courses', 'Both'],
    englishProficiency: 3,
    mathProficiency: 2,
    technicalSkills: ['Python', 'JavaScript', 'React'],
    programmingBasics: true,
    priorCourses: ['Web Development', 'Data Science'],
    learningFormat: 'short',
    weeklyTime: 10,
    learningGoals: ['Career advancement', 'Skill development'],
    learningInterests: ['Data Science', 'Web Development', 'Machine Learning']
  });

  const handleSaveProfile = async () => {
    setLoading(true);
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
        toast({
            title: "Authentication Error",
            description: "Could not find authentication token. Please log in again.",
            variant: "destructive",
        });
        setLoading(false);
        return;
    }

    try {
      const response = await fetch('http://localhost:8000/students/me', {
          method: 'PUT',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(formData),
      });

      if (!response.ok) {
          throw new Error('Failed to update profile.');
      }

      // Re-fetch user data to update the context and UI
      await fetchAndSetUser(token);

      toast({
        title: "Profile updated",
        description: "Your profile has been successfully updated.",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to update profile. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResetPreferences = () => {
    navigate('/onboarding');
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Profile Settings</h1>
          <p className="text-gray-600">Manage your account and learning preferences</p>
        </div>

        <Tabs defaultValue="profile" className="w-full">
          <TabsList>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="preferences">Learning Preferences</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Personal Information
                </CardTitle>
                <CardDescription>
                  Update your personal details and account information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-4 pt-4">
                  <div className="flex items-center gap-2">
                    <Badge variant={user?.has_completed_onboarding ? "default" : "secondary"}>
                      {user?.has_completed_onboarding ? 'Onboarding Completed' : 'Onboarding Pending'}
                    </Badge>
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <Button onClick={handleSaveProfile} disabled={loading}>
                    <Save className="h-4 w-4 mr-2" />
                    {loading ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="preferences" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Learning Preferences
                </CardTitle>
                <CardDescription>
                  Your current learning preferences based on your onboarding responses
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <Label className="text-sm font-medium">Learning Confidence</Label>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${(onboarding.learningConfidence / 5) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{onboarding.learningConfidence}/5</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label className="text-sm font-medium">Weekly Time Commitment</Label>
                    <p className="text-lg font-semibold">{onboarding.weeklyTime} hours/week</p>
                  </div>

                  <div className="space-y-3">
                    <Label className="text-sm font-medium">English Proficiency</Label>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-green-600 h-2 rounded-full" 
                          style={{ width: `${(onboarding.englishProficiency / 3) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{onboarding.englishProficiency}/3</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label className="text-sm font-medium">Math Proficiency</Label>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-purple-600 h-2 rounded-full" 
                          style={{ width: `${(onboarding.mathProficiency / 3) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{onboarding.mathProficiency}/3</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <Label className="text-sm font-medium">Technical Skills</Label>
                  <div className="flex flex-wrap gap-2">
                    {onboarding.technicalSkills.map((skill) => (
                      <Badge key={skill} variant="outline">{skill}</Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <Label className="text-sm font-medium">Learning Interests</Label>
                  <div className="flex flex-wrap gap-2">
                    {onboarding.learningInterests.map((interest) => (
                      <Badge key={interest} variant="secondary">{interest}</Badge>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <Label className="text-sm font-medium">Learning Goals</Label>
                  <div className="flex flex-wrap gap-2">
                    {onboarding.learningGoals.map((goal) => (
                      <Badge key={goal}>{goal}</Badge>
                    ))}
                  </div>
                </div>

                <div className="pt-4">
                  <Button 
                    onClick={handleResetPreferences}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Reset Preferences
                  </Button>
                  <p className="text-sm text-gray-600 mt-2">
                    This will take you through the onboarding process again to update your preferences.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity" className="space-y-6">
            <div className="grid gap-6">
              <Card>
                <CardHeader>    
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="h-5 w-5" />
                    Favorite Courses
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {favorites.length > 0 ? (
                    <div className="space-y-3">
                      {favorites.map((course) => (
                        <div key={course.id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <h4 className="font-medium">{course.title}</h4>
                            <p className="text-sm text-gray-600">{course.provider}</p>
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => navigate(`/course/${course.id}`)}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-600">No favorite courses yet</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    Recently Viewed
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {recentlyViewed.length > 0 ? (
                    <div className="space-y-3">
                      {recentlyViewed.map((course) => (
                        <div key={course.id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <h4 className="font-medium">{course.title}</h4>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <span>{course.provider}</span>
                              <span>•</span>
                              <span>Viewed on {new Date(course.viewedAt).toLocaleDateString()}</span>
                            </div>
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => navigate(`/course/${course.id}`)}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View Again
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-600">No recently viewed courses</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
};

export default Profile;
