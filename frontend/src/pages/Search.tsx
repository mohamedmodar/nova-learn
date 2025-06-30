import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { 
  Search as SearchIcon, 
  Filter, 
  Star, 
  Clock, 
  Heart,
  ExternalLink 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import CourseCard, { Course } from '../components/shared/CourseCard';
import { toast } from 'sonner';

const SearchPage = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [courses, setCourses] = useState<Course[]>([]);
  const [filteredCourses, setFilteredCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter states
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [selectedLevels, setSelectedLevels] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState('rating');

  const providers = ['Udemy', 'Coursera', 'University', 'edX', 'Pluralsight'];
  const levels = ['Beginner', 'Intermediate', 'Advanced'];
  const skills = ['Python', 'JavaScript', 'React', 'Machine Learning', 'Data Science', 'Web Development'];

  // Function to perform search and log interaction
  const performSearch = async (query: string) => {
    if (!query.trim()) {
      setCourses([]);
      setFilteredCourses([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('novalearn_token');
      
      // Search all courses
      const response = await fetch(`http://localhost:8000/search/all?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to search courses');
      }

      const data = await response.json();
      
      const transformedCourses: Course[] = data.map((c: any) => ({
        id: c.id || c.item_id,
        item_id: c.item_id || c.id,
        title: c.title,
        description: c.description,
        provider: c.provider || c.course_type,
        level: c.level || 'All Levels',
        rating: c.rating || c.adjusted_rating || 0,
        url: c.url || '',
        skills: Array.isArray(c.skills) ? c.skills : [],
        duration: c.duration || 0,
        course_type: c.course_type || 'external',
      }));
      
      setCourses(transformedCourses);
      setFilteredCourses(transformedCourses);

    } catch (error) {
      console.error("Failed to search courses:", error);
      setError("Failed to search courses. Please try again.");
      setCourses([]);
      setFilteredCourses([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle search input changes with debouncing
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.trim()) {
        performSearch(searchQuery);
      } else {
        setCourses([]);
        setFilteredCourses([]);
      }
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Remove the old mock data useEffect and replace with empty one
  useEffect(() => {
    // Initial empty state
    setCourses([]);
    setFilteredCourses([]);
  }, []);

  useEffect(() => {
    let filtered = courses.filter(course => {
      const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           course.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           (Array.isArray(course.skills) && course.skills.some(skill => skill.toLowerCase().includes(searchQuery.toLowerCase())));
      
      const matchesProvider = selectedProviders.length === 0 || (course.provider && selectedProviders.includes(course.provider));
      const matchesLevel = selectedLevels.length === 0 || (course.level && selectedLevels.includes(course.level));
      const matchesSkills = selectedSkills.length === 0 || 
                           (Array.isArray(course.skills) && selectedSkills.some(skill => course.skills.includes(skill)));

      return matchesSearch && matchesProvider && matchesLevel && matchesSkills;
    });

    // Sort courses
    filtered = filtered.sort((a, b) => {
      switch (sortBy) {
        case 'rating':
          return (b.rating || 0) - (a.rating || 0);
        case 'title':
          return a.title.localeCompare(b.title);
        case 'duration':
          return (a.duration || 0) - (b.duration || 0);
        default:
          return 0;
      }
    });

    setFilteredCourses(filtered);
  }, [searchQuery, courses, selectedProviders, selectedLevels, selectedSkills, sortBy]);

  const handleLike = async (courseId: string) => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
      toast.error("You must be logged in to like a course.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/interactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ course_id: courseId, interaction_type: 'like' }),
      });
      if (!response.ok) {
        throw new Error("Failed to save like.");
      }
      toast.success("Thanks for your feedback!");
    } catch (error: any) {
      toast.error(error.message || "Could not save feedback.");
    }
  };

  const handleDislike = async (courseId: string) => {
    const token = localStorage.getItem('novalearn_token');
    if (!token) {
      toast.error("You must be logged in to dislike a course.");
      return;
    }
    try {
      const response = await fetch('http://localhost:8000/interactions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ course_id: courseId, interaction_type: 'dislike' }),
      });
      if (!response.ok) {
        throw new Error("Failed to save dislike.");
      }
      toast.success("Feedback saved!");
    } catch (error: any) {
      toast.error(error.message || "Could not save feedback.");
    }
  };

  const handleProviderChange = (provider: string, checked: boolean) => {
    if (checked) {
      setSelectedProviders([...selectedProviders, provider]);
    } else {
      setSelectedProviders(selectedProviders.filter(p => p !== provider));
    }
  };

  const handleLevelChange = (level: string, checked: boolean) => {
    if (checked) {
      setSelectedLevels([...selectedLevels, level]);
    } else {
      setSelectedLevels(selectedLevels.filter(l => l !== level));
    }
  };

  const handleSkillChange = (skill: string, checked: boolean) => {
    if (checked) {
      setSelectedSkills([...selectedSkills, skill]);
    } else {
      setSelectedSkills(selectedSkills.filter(s => s !== skill));
    }
  };

  const clearFilters = () => {
    setSelectedProviders([]);
    setSelectedLevels([]);
    setSelectedSkills([]);
    setSearchQuery('');
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
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Discover Courses</h1>
          <p className="text-gray-600">Find the perfect course to advance your skills</p>
        </div>

        {/* Search Bar */}
        <div className="flex gap-4">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search courses, skills, or topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            Filters
          </Button>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          {showFilters && (
            <div className="lg:col-span-1">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Filters</CardTitle>
                    <Button variant="ghost" size="sm" onClick={clearFilters}>
                      Clear all
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Sort By */}
                  <div className="space-y-3">
                    <Label className="text-sm font-medium">Sort by</Label>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="rating">Highest Rated</SelectItem>
                        <SelectItem value="title">Title A-Z</SelectItem>
                        <SelectItem value="duration">Duration</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Provider Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm font-medium">Provider</Label>
                    <div className="space-y-2">
                      {providers.map((provider) => (
                        <div key={provider} className="flex items-center space-x-2">
                          <Checkbox
                            id={provider}
                            checked={selectedProviders.includes(provider)}
                            onCheckedChange={(checked) => handleProviderChange(provider, checked as boolean)}
                          />
                          <Label htmlFor={provider} className="text-sm">{provider}</Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Level Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm font-medium">Level</Label>
                    <div className="space-y-2">
                      {levels.map((level) => (
                        <div key={level} className="flex items-center space-x-2">
                          <Checkbox
                            id={level}
                            checked={selectedLevels.includes(level)}
                            onCheckedChange={(checked) => handleLevelChange(level, checked as boolean)}
                          />
                          <Label htmlFor={level} className="text-sm">{level}</Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Skills Filter */}
                  <div className="space-y-3">
                    <Label className="text-sm font-medium">Skills</Label>
                    <div className="space-y-2">
                      {skills.map((skill) => (
                        <div key={skill} className="flex items-center space-x-2">
                          <Checkbox
                            id={skill}
                            checked={selectedSkills.includes(skill)}
                            onCheckedChange={(checked) => handleSkillChange(skill, checked as boolean)}
                          />
                          <Label htmlFor={skill} className="text-sm">{skill}</Label>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Results */}
          <div className={showFilters ? "lg:col-span-3" : "lg:col-span-4"}>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-gray-600">
                {filteredCourses.length} course{filteredCourses.length !== 1 ? 's' : ''} found
              </p>
            </div>

            <div className="space-y-4">
              {filteredCourses.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  onLike={() => handleLike(course.id)}
                  onDislike={() => handleDislike(course.id)}
                />
              ))}

              {filteredCourses.length === 0 && (
                <div className="text-center py-12">
                  <SearchIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No courses found</h3>
                  <p className="text-gray-600 mb-4">Try adjusting your search or filters</p>
                  <Button onClick={clearFilters}>Clear filters</Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default SearchPage;
