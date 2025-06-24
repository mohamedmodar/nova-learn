
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
  isExternal: boolean;
}

const SearchPage = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [courses, setCourses] = useState<Course[]>([]);
  const [filteredCourses, setFilteredCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter states
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [selectedLevels, setSelectedLevels] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState('rating');

  const providers = ['Udemy', 'Coursera', 'University', 'edX', 'Pluralsight'];
  const levels = ['Beginner', 'Intermediate', 'Advanced'];
  const skills = ['Python', 'JavaScript', 'React', 'Machine Learning', 'Data Science', 'Web Development'];

  useEffect(() => {
    const fetchCourses = async () => {
      // Mock API call
      const mockCourses: Course[] = [
        {
          id: '3',
          title: 'Complete React Developer Course',
          description: 'Build modern web applications with React, Redux, and more',
          provider: 'Udemy',
          level: 'Intermediate',
          rating: 4.6,
          adjustedRating: 4.8,
          duration: '40 hours',
          skills: ['React', 'JavaScript', 'Redux', 'Web Development'],
          isExternal: true
        },
        {
          id: '4',
          title: 'Python for Data Science',
          description: 'Master Python programming for data analysis and visualization',
          provider: 'Coursera',
          level: 'Beginner',
          rating: 4.4,
          adjustedRating: 4.6,
          duration: '6 weeks',
          skills: ['Python', 'Data Analysis', 'Pandas', 'NumPy'],
          isExternal: true
        },
        {
          id: '5',
          title: 'Machine Learning A-Z',
          description: 'Hands-on machine learning with Python and R',
          provider: 'Udemy',
          level: 'Advanced',
          rating: 4.5,
          adjustedRating: 4.7,
          duration: '44 hours',
          skills: ['Machine Learning', 'Python', 'Statistics', 'AI'],
          isExternal: true
        },
        {
          id: '6',
          title: 'Full Stack Web Development',
          description: 'Complete guide to modern web development',
          provider: 'University',
          level: 'Intermediate',
          rating: 4.3,
          adjustedRating: 4.3,
          duration: '16 weeks',
          skills: ['JavaScript', 'Node.js', 'React', 'MongoDB'],
          isExternal: false
        },
        {
          id: '7',
          title: 'Introduction to AI',
          description: 'Fundamentals of artificial intelligence and neural networks',
          provider: 'edX',
          level: 'Beginner',
          rating: 4.2,
          adjustedRating: 4.4,
          duration: '8 weeks',
          skills: ['AI', 'Machine Learning', 'Neural Networks'],
          isExternal: true
        }
      ];

      setCourses(mockCourses);
      setFilteredCourses(mockCourses);
      setLoading(false);
    };

    fetchCourses();
  }, []);

  useEffect(() => {
    let filtered = courses.filter(course => {
      const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           course.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           course.skills.some(skill => skill.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesProvider = selectedProviders.length === 0 || selectedProviders.includes(course.provider);
      const matchesLevel = selectedLevels.length === 0 || selectedLevels.includes(course.level);
      const matchesSkills = selectedSkills.length === 0 || 
                           selectedSkills.some(skill => course.skills.includes(skill));

      return matchesSearch && matchesProvider && matchesLevel && matchesSkills;
    });

    // Sort courses
    filtered = filtered.sort((a, b) => {
      switch (sortBy) {
        case 'rating':
          return b.adjustedRating - a.adjustedRating;
        case 'title':
          return a.title.localeCompare(b.title);
        case 'duration':
          return a.duration.localeCompare(b.duration);
        default:
          return 0;
      }
    });

    setFilteredCourses(filtered);
  }, [searchQuery, courses, selectedProviders, selectedLevels, selectedSkills, sortBy]);

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
                <Card key={course.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="secondary">{course.provider}</Badge>
                          <Badge>{course.level}</Badge>
                        </div>
                        <CardTitle className="text-lg mb-2">{course.title}</CardTitle>
                        <CardDescription className="line-clamp-2">
                          {course.description}
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-red-500"
                      >
                        <Heart className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-1">
                        {course.skills.slice(0, 4).map((skill) => (
                          <Badge key={skill} variant="outline" className="text-xs">
                            {skill}
                          </Badge>
                        ))}
                        {course.skills.length > 4 && (
                          <Badge variant="outline" className="text-xs">
                            +{course.skills.length - 4} more
                          </Badge>
                        )}
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                            {course.adjustedRating}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {course.duration}
                          </div>
                        </div>
                        <Button 
                          onClick={() => navigate(`/course/${course.id}`)}
                          className={course.isExternal ? "bg-green-600 hover:bg-green-700" : ""}
                        >
                          {course.isExternal ? (
                            <>
                              <ExternalLink className="h-4 w-4 mr-2" />
                              View Course
                            </>
                          ) : (
                            'View Details'
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
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
