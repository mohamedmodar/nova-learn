
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import OnboardingStep1 from '../components/onboarding/OnboardingStep1';
import OnboardingStep2 from '../components/onboarding/OnboardingStep2';
import OnboardingStep3 from '../components/onboarding/OnboardingStep3';
import OnboardingStep4 from '../components/onboarding/OnboardingStep4';

export interface OnboardingData {
  learningConfidence: number;
  coursePreference: string[];
  englishProficiency: number;
  mathProficiency: number;
  technicalSkills: string[];
  programmingBasics: boolean;
  priorCourses: string[];
  learningFormat: string;
  weeklyTime: number;
  learningGoals: string[];
  learningInterests: string[];
}

const Onboarding = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [data, setData] = useState<OnboardingData>({
    learningConfidence: 3,
    coursePreference: [],
    englishProficiency: 3,
    mathProficiency: 3,
    technicalSkills: [],
    programmingBasics: false,
    priorCourses: [],
    learningFormat: '',
    weeklyTime: 5,
    learningGoals: [],
    learningInterests: []
  });
  const [loading, setLoading] = useState(false);
  const { updateUser } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const totalSteps = 4;
  const progress = (currentStep / totalSteps) * 100;

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    
    try {
      // Save onboarding data - replace with actual API call
      console.log('Onboarding data:', data);
      
      updateUser({ hasCompletedOnboarding: true });
      
      toast({
        title: "Profile completed!",
        description: "Your personalized recommendations are ready.",
      });
      
      navigate('/home');
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save your preferences. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const updateData = (newData: Partial<OnboardingData>) => {
    setData({ ...data, ...newData });
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <OnboardingStep1 data={data} updateData={updateData} />;
      case 2:
        return <OnboardingStep2 data={data} updateData={updateData} />;
      case 3:
        return <OnboardingStep3 data={data} updateData={updateData} />;
      case 4:
        return <OnboardingStep4 data={data} updateData={updateData} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Let's personalize your experience</h1>
          <p className="text-gray-600">Help us understand your learning preferences to provide better recommendations</p>
        </div>

        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Step {currentStep} of {totalSteps}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Step {currentStep}</CardTitle>
            <CardDescription>
              {currentStep === 1 && "Tell us about your learning background"}
              {currentStep === 2 && "What are your technical skills?"}
              {currentStep === 3 && "How do you prefer to learn?"}
              {currentStep === 4 && "What are your learning goals?"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {renderStep()}
          </CardContent>
        </Card>

        <div className="flex justify-between mt-8">
          <Button
            variant="outline"
            onClick={handlePrev}
            disabled={currentStep === 1}
            className="flex items-center gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>
          
          {currentStep === totalSteps ? (
            <Button
              onClick={handleComplete}
              disabled={loading}
              className="bg-green-600 hover:bg-green-700 flex items-center gap-2"
            >
              {loading ? 'Completing...' : 'Complete Setup'}
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
