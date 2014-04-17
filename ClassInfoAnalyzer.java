import java.io.File;
import java.io.IOException;

import javax.tools.ToolProvider;
import javax.tools.JavaCompiler;

import java.lang.reflect.*;
import java.util.regex.*;

/**
 * Prints out all of the info about a class's methods, and those methods
 * parameters.
 */
public class ClassInfoAnalyzer {
    /**
     * This regular expression identifies primative types and strings, as well
     * as arrays containing those primatives types and strings.
     */
    private static final String primativeTypes =
        "(long|int|short|byte|char|float|double|boolean|(.*String.*))(\\[\\d*\\])?";

    private static final Pattern pattern = Pattern.compile( primativeTypes );

    /** Empty Constructor */
    private ClassInfoAnalyzer() { }

    /**
     * Analyzes the constructors for objects
     */
    private static String analyzeConstructors( Class<?> clazz, int tabDepth ) {
        Constructor<?>[] constructors = clazz.getConstructors();
        StringBuilder str = new StringBuilder("");

        //For every constructor...
        for ( Constructor constructor : constructors ) {
            //pad that shit and....
            for (int i = 0; i < tabDepth; i++) {
                System.out.print("\t");
                str.append("\t");
            }

            //Print out information about the constructor.
            System.out.println(constructor);
            str.append( constructor ).append( "\n" );
        }

        return str.toString();
    }

    /**
     * Prints out information about the contained classes methods
     */
    public static String analyzeMethods( Class<?> classToAnalyze ) {
        StringBuilder dictionary = new StringBuilder();
        Method[] methods = classToAnalyze.getDeclaredMethods();

        // For every method in the class...
        for( Method method : methods ) {
            System.out.println( method.getName() + ":" );

            // Map the method name to a dictionary
            dictionary.append( "{\"" + method.getName() ).append("\":{(");

            for ( int i = 0; i < method.getName().length() + 1; i++)  {
                System.out.print("-");
            }
            System.out.println();

            // Get it's parameters.
            Class<?>[] methodParameters = method.getParameterTypes();

            if( methodParameters.length > 0 )
                System.out.println("Takes as parameters:");

            // For each parameter...
            for( Class<?> methodParameter : methodParameters ) {
                Matcher m = pattern.matcher( methodParameter.toString() );

                dictionary.append( "\"" + methodParameter.toString() + "\"," );

                // Print its name if it is a primative type
                if( m.matches() ) {
                    System.out.println( "\t" + methodParameter );

                }

                //And analyze the constructors of it otherwise
                else {
                    analyzeConstructors( methodParameter, 2 );
                }
            }

            // End the tuple and map that to the return value
            dictionary.append( "):" );

            // Prints out return value
            System.out.println( "Returns:");
            System.out.println( "\t" + method.getReturnType() );

            dictionary.append( "\"" + method.getReturnType() ).append( "\"}}," );
            System.out.println("---------------------------------------------");
        }

        // End the dictionary string and print it
        String dictionaryString = dictionary.toString();
        dictionaryString.replaceAll( ",(\\))", "\\1" );
        System.out.println(dictionary);

        return dictionary.toString();
    }

    public static void main (String[] args) {
        String filename = args[0];

        //Verify that args array is at least length 1
        if( args.length < 1 ) {
            System.out.println("Usage: java ClassInfoAnalyzer <class_filename>");
            System.exit(0);
        }

        else {
            /*
             * Load the class using the class loader and then pass that
             * class to the analyzeMethods function. The std out from that
             * function is a Python dictionary that maps the class in the
             * following way:
             *
             * { Method -> { (argument list) -> return type } }
             *
             * That is, the method maps to a dictionary, that maps a tuple
             * containing argument types to the return type of the method.
             */

            //Iterate over each String in args and attempt to perform the
            //analyze methods procedure on it
            for ( String classname : args ) {
                System.out.println("Generating the report for " + classname + ":" );

                try {
                    //Get the system's class loader and load the users class
                    ClassLoader loader = ToolProvider.getSystemToolClassLoader();
                    Class<?> classToAnalyze = loader.loadClass( filename );

                    //Analyze class and create dictionary
                    ClassInfoAnalyzer.analyzeMethods( classToAnalyze );
                }
                catch(ClassNotFoundException cnfe) {
                    System.err.println("Error! Undefined class passed to analyzer!");
                }
            }
        }
    }
}
