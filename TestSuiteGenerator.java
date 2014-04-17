import java.io.File;
import java.io.IOException;

import javax.tools.ToolProvider;

import java.util.Scanner;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;

/**
 * Generates test suites.
 */
public class TestSuiteGenerator {

    //System class loader object
    private final ClassLoader loader = ToolProvider.getSystemToolClassLoader();

    private String suiteName;
    private List<String> imports;
    private Map<String, String> testCases;

    /**
     * Creates a generator for a test suite
     * @param suiteName The name of the test suite
     */
    public TestSuiteGenerator( String suiteName ) {
        this.suiteName  = suiteName;
        this.testCases  = new HashMap<>();
        this.imports    = new ArrayList<>();
    }

    /**
     * Generates a test suite containing a few test tests.
     */
    public static void main (String[] args) {
        //Create the generator
        TestSuiteGenerator generator = new TestSuiteGenerator("Test");

        //Create a test that handles a object being invoked on object instance
        generator.generateStandardTest( String.class, "s", "substring",
                "Substring", "0, 5", "\"gener\"", "\"generated\"" );

        //Import something
        generator.addImport( "java.util.Random" );

        //Create a test that handles being invoked on the class statically.
        generator.generateStaticTest( Integer.class, "ParseInt", "5",
                "parseInt", "\"5\"" );

        //Create a test that involves loading something on the class loader
        generator.generateStaticTest( "java.lang.Character", "IsLowerCase",
                "true", "isLowerCase", "\'c\'" );

        //Generate and print out the resulting runnable test suite
        String result = generator.generateTestSuite();
        System.out.println(result);
    }

    /**
     * Adds an import to the list of libraries that will be imported inside the
     * testing suite. For example, setting up the test suite to import random is
     * accomplished by making the following call:
     * <tt>             addImport( "java.util.Random" );</tt>
     * @param libraryToImport The library that you would like to be imported
     * within the test suite.
     */
    public void addImport( String libraryToImport ) {
        this.imports.add( libraryToImport );
    }

    /**
     * Attempts to load the class with the specified name using the system's
     * specified class loader.
     * @param classToLoad The name of the class to load
     * @return The class with the specified name or null if that class could not
     * be loaded.
     */
    private Class<?> loadClassFromString( String classToLoad ) {
        Class<?> loadedResult = null;

        try {
            loadedResult = this.loader.loadClass( classToLoad );
        }
        catch( ClassNotFoundException cnfe) {
            System.err.println( "In TestSuiteGenerator.loadClassFromString:");
            cnfe.printStackTrace();
        }

        return loadedResult;
    }

    /**
     * Generates a test suite based on the tests previously added to the object.
     * @return A string containing the source code for a test suite
     * containing the previously created tests.
     */
    public String generateTestSuite() {
        //Add necessary header information
        StringBuilder sb = new StringBuilder();

        //Add user defined imports
        for ( String libraryToImport : this.imports )  {
            sb.append( "import " ).append( libraryToImport ).append(";\n");
        }

        //Add class declaration
        sb.append( "\npublic class ").append( this.suiteName ).append( " {\n\n" );

        //Add smartAssert
        sb.append( "    public static void smartAssert( Object a, Object b ) {\n" );
        sb.append( "        boolean result = a.equals(b);\n" );
        sb.append( "        if( ! result ) {\n" );
        sb.append( "            throw new AssertionException( \"Assertion Error: a.equals(b) returned false!\");\n" );
        sb.append( "        }\n" );
        sb.append( "    }\n\n" );

        //Write each test case to the StringBuilder
        for ( String testCase : this.testCases.values() ) {
            sb.append( testCase ).append("\n" );
        }

        //Generate the main method
        sb.append( "    public static void main( String[] args ) {\n" );

        //Make calls to the generated test methods in the suite
        for ( String testName : this.testCases.keySet() )  {
            sb.append( "        " + testName + "();\n" );
        }

        sb.append( "    }\n" );
        sb.append( "}" );

        return sb.toString();
    }

    /**
     * Generates a single test standard test case for the user.
     * @param clazz The class that this test is evaluating.
     * @param instanceName The name of the instance of <tt>clazz</tt> that will
     * be created.
     * @param methodName The name of the method that is being evaluated
     * @param testName The test that is running
     * @param methodArguments The string of arguments that are passed to
     * <tt>methodName</tt>.
     * @param expectedValue The value expected to return from the target
     * method.
     * @param constructorArguments The string of arguments that are passed to
     * the object constructor.
     */
    public void generateStandardTest( Class<?> clazz, String instanceName,
            String methodName, String testName, String methodArguments, String
            expectedValue, String constructorArguments ) {

        //Load the proper template file
        String template = loadTemplateFile( "StandardTestTemplate.txt" );

        //Replace template tags
        template = replaceTagWith( template, "testName", testName );
        template = replaceTagWith( template, "className", clazz.getSimpleName() );
        template = replaceTagWith( template, "name", testName );
        template = replaceTagWith( template, "methodName", methodName );
        template = replaceTagWith( template, "expected", expectedValue);
        template = replaceTagWith( template, "cons_list", constructorArguments );
        template = replaceTagWith( template, "m_list", methodArguments );

        //Add the completed template to the test cases
        this.testCases.put( "test" + testName, template );
    }


    /**
     * @param className The name of the lass that will be loaded by the
     * classloader.
     * @param instanceName The name of the instance of <tt>clazz</tt> that will
     * be created.
     * @param methodName The name of the method that is being evaluated
     * @param testName The test that is running
     * @param methodArguments The string of arguments that are passed to
     * <tt>methodName</tt>.
     * @param expectedValue The value expected to return from the target
     * method.
     * @param constructorArguments The string of arguments that are passed to
     * the object constructor.
     */
    public void generateStandardTest( String className, String instanceName,
            String methodName, String testName, String methodArguments, String
            expectedValue, String constructorArguments ) {
        this.generateStandardTest( loadClassFromString( className ),
                instanceName, methodName, testName, methodArguments,
                expectedValue, constructorArguments );
    }

    /**
     * @param clazz The class that this test is evaluating.
     * be created.
     * @param testName The test that is running
     * @param methodName The name of the method that is being evaluated
     * @param methodArguments The string of arguments that are passed to
     * <tt>methodName</tt>.
     * @param expectedValue The value expected to return from the target
     * method.
     */
    public void generateStaticTest( Class<?> clazz, String testName,
            String expectedValue, String methodName, String methodArguments ) {

        String template = loadTemplateFile( "StaticTestTemplate.txt" );

        //Replace template tags
        template = replaceTagWith( template, "testName", testName );
        template = replaceTagWith( template, "className", clazz.getSimpleName() );
        template = replaceTagWith( template, "name", testName );
        template = replaceTagWith( template, "methodName", methodName );
        template = replaceTagWith( template, "expected", expectedValue);
        template = replaceTagWith( template, "m_list", methodArguments );

        //Add the completed template to the test cases
        this.testCases.put( "test" + testName, template );
    }

    /**
     * @param className The name of the class that will be loaded by the
     * class loader
     * @param testName The test that is running
     * @param methodName The name of the method that is being evaluated
     * @param methodArguments The string of arguments that are passed to
     * <tt>methodName</tt>.
     * @param expectedValue The value expected to return from the target
     * method.
     */
    public void generateStaticTest( String className, String testName,
            String expectedValue, String methodName, String methodArguments ) {
        this.generateStaticTest( loadClassFromString( className ), testName,
                expectedValue, methodName, methodArguments );
    }
    /**
     * Loads a template from a file into a string.
     * @param templateName The name of the template to load (including file
     * extension, but excluding parent folders).
     * @return The contents of the file in a string.
     */
    private String loadTemplateFile( String templateName ) {
        File file = new File( "generation_templates/" + templateName );
        StringBuilder sb = new StringBuilder();
        try( Scanner fileScan = new Scanner(file) ) {

            //Read every line from the file and append it to the StringBuilder
            while( fileScan.hasNextLine() ) {
                String line = fileScan.nextLine();

                if( line.endsWith("\n") ) {
                    sb.append( line );
                }
                else {
                    sb.append( line + "\n" );
                }
            }
        }
        catch( IOException ioe ) {
            System.err.println( "In TestSuiteGenerator.loadTemplateFile: " );
            ioe.printStackTrace();
        }

        return sb.toString();

    }

    /**
     * Replaces the specified tag with a replacement if it is found in the
     * target string.
     * @param target The string to search and replace within
     * @param tag The tag that would be found inside the curly braces, to
     * replace within the target string.
     * @param replacement The string that replaces the tag if it is found in the
     * target string.
     * @return The string with the specified tag replaced
     */
    private String replaceTagWith( String target, String tag, String replacement ) {
        return target.replaceAll( "\\{" + tag + "\\}", replacement );
    }
}
