import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;

import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;

import java.io.*;

/**
 * Provides a simplistic, and callable API for test suite generation is
 * extremely simple use cases where excessive customization is not needed.
 */
public class SuiteGeneratorAPI {

    private static ClassLoader loader = ToolProvider.getSystemToolClassLoader();
    private static JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();

    /**
     * Generates, compiles, and executes a singular test case.
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
    public static String runAStandardTest( String className, String
            instanceName, String methodName, String testName, String
            methodArguments, String expectedValue, String constructorArguments,
            String suiteName ) {
        //Create the suite generator
        TestSuiteGenerator generator = new TestSuiteGenerator( suiteName );

        //Generate the test
        generator.generateStandardTest( className, instanceName, methodName,
                testName, methodArguments, expectedValue, constructorArguments );

        //Generate the suite
        String generatedTestSuite = generator.generateTestSuite();

        //Compe and run the suite
        return compileAndRun( generatedTestSuite, suiteName );
    }

    /**
     * Generates, compiles, and executes a singular static test.
     * @param className The name of the class that will be loaded by the
     * class loader
     * @param testName The test that is running
     * @param methodName The name of the method that is being evaluated
     * @param methodArguments The string of arguments that are passed to
     * <tt>methodName</tt>.
     * @param expectedValue The value expected to return from the target
     * method.
     * @param suiteName The name of the test suite generated and ran.
     */
    public static String runAStaticTest( String className, String testName,
            String expectedValue, String methodName, String methodArguments,
            String suiteName ) {
        //Create the suite generator
        TestSuiteGenerator generator = new TestSuiteGenerator( suiteName );

        //Generate the test
        generator.generateStaticTest( className, testName, expectedValue,
                methodName, methodArguments );

        //Generate the suite
        String generatedTestSuite = generator.generateTestSuite();

        //Compile and run the suite
        return compileAndRun( generatedTestSuite, suiteName );
    }

    private static String compileAndRun( String testSuiteSrc, String suiteName ) {
        //Create the file object
        File javaFile = new File( suiteName + ".java" );

        try {
            javaFile.createNewFile();

            //Write the test suite into the file
            FileWriter writer = new FileWriter( javaFile );
            writer.write( testSuiteSrc );
            writer.flush();
            writer.close();
        }
        catch(IOException ioe) {
            System.err.println("In SuiteGeneratorAPI.runAStaticTest" );
            ioe.printStackTrace();
        }

        //Now compile that file and verify it successfully compiled.
        int compilationResult = compileSrcFile( suiteName + ".java" );

        if( compilationResult != 0 ) {
            return "Compilation failed!";
        }

        //Redirect standard out...because reasons...
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        System.setOut( new PrintStream(baos) );

        //Run the file
        try {
            //Load the class file
            Class<?> compiledTestSuite = loader.loadClass( suiteName );

            //Access the main method inside the loaded class file
            Method mainMethod = compiledTestSuite.getMethod( "main", String[].class );

            //Set up the arguments for main
            final Object[] args = new Object[1];
            args[0] = new String[] {};

            //Invoke the main method
            mainMethod.invoke( null, args );
        }
        catch( InvocationTargetException ite ) {
            //Unwrap and rethrow this as the exception it knows it can be.
            throw (RuntimeException)ite.getCause();
        }
        catch( ClassNotFoundException cnfe ) {
            System.out.println( "Could not locate the class to load it." );
        }
        catch( NoSuchMethodException nsme ) {
            System.out.println( "Could not find the main method in the class file" );
        }
        catch( IllegalAccessException iae ) {
            System.out.println( "Could not access class details!" );
        }

        //Get the output of the file
        String resultOfTest = baos.toString();

        //Return standard out back to normal
        PrintStream ps = new PrintStream( new FileOutputStream( FileDescriptor.out ) );
        System.setOut( ps );

        return resultOfTest;
    }

    public static void main (String[] args) {
        //Print out information about the current arguments

        //8 arguments indicates a standard test case
        if( args.length == 8 ) {
            //Unpack the argument list
            String className            = args[0];
            String instanceName         = args[1];
            String methodName           = args[2];
            String testName             = args[3];
            String methodArguments      = args[4];
            String expectedValue        = args[5];
            String constructorArguments = args[6];
            String suiteName            = args[7];

            //Call the standard suite generator with these arguments
            String out = runAStandardTest( className, instanceName, methodName,
                    testName, methodArguments, expectedValue,
                    constructorArguments, suiteName );
        }

        //6 arguments indicates testing of a static method
        else if( args.length == 6 ) {
            //Unpack the argument list
            String className        = args[0];
            String testName         = args[1];
            String expectedValue    = args[2];
            String methodName       = args[3];
            String methodArguments  = args[4];
            String suiteName        = args[5];

            //Call the static suite generator with these arguments
            String out = runAStaticTest( className, testName, expectedValue,
                    methodName, methodArguments, suiteName );
        }

        //Otherwise fail
        else {
            System.out.println( "Invalid argument setup!" );
        }
    }

    /**
     * Compiles the specified java file
     * @param filename The name of the file that you would like to compile.
     * @return The result of the compilation.
     */
    private static int compileSrcFile( String filename ) {
        return compiler.run( null, null, null, filename );
    }
}
