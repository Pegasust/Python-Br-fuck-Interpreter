"""
    filename: lite_unit_test.py
    author: Hung Tran
    purpose: to ease the unit testing and debugging work.

    =====================================================
                BACKWARD COMPATIBILITY CONCERNS
        The order of arguments from UnitTest.add_test might
    have changed. Double check the arugment positions before
    being concerned of your functions.
    =====================================================

    Classes:
        TestEntry:
            __init__(self,...)
            multi_init -> set<TestEntry>
            lazy_init -> TestEntry
        UnitTest:
            __init__(self)
            add_test(self,...)
            add_tests(self,iterable<TestEntry>)
            execute(self)
            execute_async(self, timeout): HIGHLY DISCOURAGED.
    Functions:
        try_import(module_path)
        in_set_wrapper(rhs,lhs)
        str_eq(lhs,rhs)
        str_in_set(lhs,rhs)
    Objects:
        UTEST_INSTANCE: UnitTest

    usage: 
    <1>: for in-script testing (preferred)
        1. import this module.
        2. use UTEST_INSTANCE provided by the module or
            create a new UnitTest
        3. add all tests with UnitTest.add_test() or (3.5)
            3.5. Create specific TestEntry-s and add with
            UnitTest.add_tests(Iterable<TestEntry>)
                3.5.0. Use TestEntry.__init__,
                TestEntry.multi_init (produces set of entries)
                3.5.1. Use helper funcs like in_set_wrapper, str_eq,
                str_in_set for equal_func_ptr or write your own
                evaluation funcs
        4. after adding all of the test cases, UnitTest_obj.execute()
        to synchronously process all the tests.
        
        Note: Use UnitTest_obj.execute_async() at your own caution.
        UnitTest_obj.execute*() can only be used once. A new UnitTest
        obj should be created for different test phrases.

        Advanced: create multiple instances of UnitTest and split
        tests on your own and run them multithreadedly.

    <2>: for writing assignment checker (advanced, outdated):
        1. import this module.
        2. in the checker, use try_import.
        3. write test_cases with return value of try_import as the
            imported module. example: try_import("merge.py").
        3. encapsulate all test cases and execute() of that module in
            if(try_import is not none)

    potential improvement:
        + Write on stderr upon exceptions
        + Abort function upon timeout
        + Make Exception prints more visible.
"""
import importlib
import threading
import multiprocessing
import traceback
import os
import queue
import time
from typing import *

def try_import(module_path):
    """ try import module_path and return the module. returns none
         and prints Exception error if import cannot be accomplished.
         
        argument: module_path is string that is absolute or relative
                        path of the module we want to import

        returns: module or none
    """
    try:
        return importlib.import_module(module_path)            
    except Exception as e:
        Exception_str = "could not import \"{}\". error: {}; {}"\
            .format(module_path, e.__doc__, e)
        print(Exception_str)
        return None

   
# ========EQUAL_FUNC_HELPERS=========================================
def in_set_wrapper(element, set_):
    return str(element) in set_

def str_eq(lhs, rhs):
    return str(lhs) == str(rhs)

def str_in_set(lhs, rhs_iter):
    return str(lhs) in set(map(str,rhs_set))

# ===================================================================
class TestEntry:
    """
        a struct that contains the meta data of a test entry.
	this should be used to store in the task queue.
	variables:
        - func_ptr: pointer to the executing function
		- func_arg: tuple of arguments to func_ptr to be passed
		- equal_func_rhs: (set) value to be expected to return True
			from equal_func_ptr.
		- equal_func_ptr: pointer to evaluate actual func output to
			expected_func_output. execute() calls 
			self.equal_func_ptr(output, *self.equal_func_rhs)
		- func_name: custom name for func_ptr (in case func_ptr is
				pointer to a lambda)

    """
    def __init__(self, func_ptr, equal_func_ptr,\
       equal_func_rhs, func_name=None, *func_arg):
        """
            Arguments:
                -func_ptr is pointer to a function. This func should be
                seen on the global scope because multiprocessing most likely
                will require the function to be from __main_mp__
                -func_arg: tuple of arguments that is sent by position
                to func_ptr.
                -equal_func_ptr: function that checks the output of the func
                -equal_func_rhs: value which when passed to equal_func_ptr
                on the 2nd position will return True:                    
                    Ex: 
                    equal_func_ptr == lambda lhs,rhs : str(lhs) == str(rhs)
                    equal_func_rhs will be passed like this:
                        equal_func_ptr(func_output,equal_func_rhs)
                -func_name: (optional)
                the name of func_ptr, in case func_ptr is a lambda.
                Pass in None to default to func_ptr.__name__ (lambdas will
                have weird func name).
                -*func_arg is positional argument. You can pass in two ways:
                    (1)__init__(...,*func_arg=a,b,c) -> func_ptr(a,b,c)
                    (2)__init__(...,*func_arg=(a,b,c)) -> func_ptr(*(a,b,c))
                                                       -> func_ptr(a,b,c)

            Note:
                -For equal_func_ptr, use helper functions from this module:
                    +str_eq: converts lhs and rhs to string and do 
                    string comparison
                    +in_set_wrapper: see if (lhs in rhs). This is useful
                    for unordered or partial outputs.
                    +str_in_set: same with in_set_wrapper but converts
                    lhs and each element on rhs to string before using "in"
                -Use TestEntry.multi_init to get set of UnitTests with the same
                    func_ptr and equal_ptr and unique test cases.
                -Use UnitTest.add_test for lazy_init instead. It helps reduce
                lines of codes.

            Personal Note:
                -Thanks for taking your time reading this. I figured 
                since I used this tool a lot in my assignment to check 
                if the func works well when I'm offline, it would be 
                beneficial for everyone to have access to this file.
        """
        if func_name is None:
            func_name = func_ptr.__name__
        self.func_ptr = func_ptr
        self.equal_func_ptr = equal_func_ptr
        self.equal_func_rhs = equal_func_rhs
        self.func_name = func_name
        self.func_arg = func_arg

    def __str__(self):
        _ = f'TestEntry: {self.func_name}({self.func_arg})'
        _ += f'should yield True on {self.equal_func_ptr}'
        _ += f'({self.equal_func_rhs})'
        return _
    # an alternative function to construct a TestEntry
    @classmethod
    def lazy_init(cls,func_ptr,expected_str_out_set,*func_arg):
        """
            cls is the class alias to be passed by @classmethod
            lazy_init initializes a TestEntry with equal_func 
            of in_set_wrapper and func_name of func_ptr.__name__
            Arguments:
                - func_ptr: pointer to function needs to execute
                that outputs a certain _output
                - expected_str_out_set: set of strings such that 
                the str(_output) would be in expected_str_out_set
                - *func_arg: positional arguments to func_ptr.
        """
        return cls(func_ptr,in_set_wrapper,expected_str_out_set,\
                   func_ptr.__name__, *func_arg)

    @classmethod
    def multi_init(cls,func_ptr:Callable[...,Any],\
        equal_func_ptr:Callable[...,Any],\
        func_arg_2_equal_rhs:Dict[tuple,Any]\
        ,func_name:str=None,\
        get_each_equal_rhs = False)\
       -> set:
        """
            Initialize multiple TestEntry and return a
            set of TestEntry's.
        """

        if func_name is None:
            func_name = func_ptr.__name__
        ret_val = set()
        for func_arg, equal_rhs in func_arg_2_equal_rhs.items():
            if get_each_equal_rhs:
                # check if equal_rhs is iterable
                try:
                    i = iter(equal_rhs)
                    for rhs in i:
                        ret_val.add(cls(\
                            func_ptr,equal_func_ptr,rhs,func_name,*func_arg))
                    # ignore anything below
                    continue
                except TypeError:
                    pass
            # if not get_each_equal_rhs or (is not iterable)
            # add only one test per func_arg tuple
            ret_val.add(cls(func_ptr,\
                            equal_func_ptr,equal_rhs,func_name,*func_arg))
        return ret_val
    def execute(self, utest, timedout = None):
        try:
            # Create a string expression of the function: func(*func_arg)
            func_str = "{}({})".format(self.func_name,\
               ", ".join(map(str,self.func_arg)))
            # Get output from executing the function
            output = self.func_ptr(*self.func_arg)
            # check if timed out
            if timedout is not None and timedout[0]:
                utest.print_queue.put("Failed: ({}) timed out.".
                                      format(func_str))
                return None
            # Evaluate whether output is expected
            output_is_expected = self.equal_func_ptr(\
                output,self.equal_func_rhs)
            # Add the output to the function string
            func_str += "->{}".format(output)
            if output_is_expected:
                utest.passed.put("Passed: {}".format(func_str))
            else:
                utest.print_queue.put("Failed: {} is not evaluated from {}\n".\
                                      format(func_str,self.equal_func_rhs))
        except Exception as e:
                # catch all Exceptions in theory
                msg = ("Failed: {}".format(str(self)))
                msg += "\nerror: {} {}\n".format(e.__doc__, e)
                msg += traceback.format_exc()
                msg += '\n'
                # should be better to print in stderr
                utest.print_queue.put(msg)
        finally:
            pass
def _execute_synchronously(test_q,utest, timeout = None):
    utest.print_queue.put("PID #{} should be started.".format(os.getpid()))
    logger = multiprocessing.get_logger()
    while not test_q.empty():
        try:
            test = test_q.get()
            timedout = [False]
            execute_thread = threading.Thread(target = test.execute,
                                             args = (utest,timedout))
            execute_thread.start()
            execute_thread.join(timeout)
            # if test.execute is not done after timeout
            if execute_thread.is_alive():
                # Abort the thread
                timedout[0] = True
        except Exception as e:
            logger.error(e)
    # test_q is now empty.
    utest.print_queue.put("PID #{} should be joined.".format(os.getpid()))
    return True

def _all_processes_are_dead(processes:multiprocessing.Process)-> bool:
    for p in processes:
        if p.is_alive():
            return False
    return True

class UnitTest:
    """
        a class that helps compare output of a function given an input.
        uses a dict to traverse through function calls and arguments.
        does not break any test in case an Exception is thrown and prints
        out Exceptions.
        
        notes: add_test() for every possible tests before execute()
        
        static consts:
            - PROCESSES = computer's core count - 2. 
            2 is the number of print threads
        variables: 
            -test_queue fifo with multiple consumers
				of (TestEntry)
            -print_queue: fifo with multiple producers
                and single consumer of string
            -total is int of total tests added
            -passed is queue of total tests passed output
            -count is the number of passed test wrapped by a collection
                to be passed by reference.
    """
    PROCESSES = multiprocessing.cpu_count()-1

    def __init__(self):
        self.test_queue = multiprocessing.Queue()
        self.print_queue = multiprocessing.Queue()
        self.total = 0
        self.passed = multiprocessing.Queue()
        self.count = 0

    def add_test(self, func, expected_str_out_set, *f_arg):
        """
            lazily adds the test to test_queue without executing it.
            converts expected_str_out_set to str_set if necessary.

            arguments:
                func is function pointer (pass by name without ())
                expected_str_out_set is the set contains
					all expected string outputs
                    from func(f_arg).
                f_arg is tuple of function arguments
            
            pre-condition:
                func is func ptr of any kind
                f_arg can be tuple or positional arguments
                expected_str_out_set must be str or any type with
                    __str__() declared
            
            post-condition:
				self.test_queue has one added test
                self.total += 1
        """
        # ensures expected_str_out is actually set of str
        # this also allows lazy typing and unsure in str notation
        # of the resulting obj
        if type(expected_str_out_set) is not set:
            expected_str_out_set = {expected_str_out_set}
        str_set = set()
        while len(expected_str_out_set) > 0:
            # Converts every element to str
            expected_str_out = expected_str_out_set.pop()
            if type(expected_str_out) is not str:
                expected_str_out = str(expected_str_out)
            str_set.add(expected_str_out)
        entry = TestEntry.lazy_init(func, str_set, *f_arg)
        self.test_queue.put(entry)
        self.total += 1

    def add_tests(self, *entries):
        """
            Note: pass in utest_instance.add_tests(*TestEntry.multi_init())
            to correctly add tests generated by multi_init(), because
            add_tests takes positional arguments of entries.
        """
        for entry in entries:
            self.test_queue.put(entry)
            self.total+=1

    def execute(self):
        """
            Executes all TestEntries sequentially.
            Note: This does not implement timeout. Besure all tests
            do not face an infinite loop.
        """
        # Synchronously calling this, so it should not create
        # any random thread.
        _execute_synchronously(self.test_queue, self)
        # _execute_synchronously assigns to print_queue and passed
        # Read messages from both queues sequentially.
        while not self.print_queue.empty():
            print(self.print_queue.get())
        while not self.passed.empty():
            print(self.passed.get())
            self.count += 1
        print("passed {}/{}".format(self.count, self.total))
        return None

    def execute_async(self, timeout_per_test_sec:float = 10):
        """
            Executes all TestEntries asynchronously (inaccurate & unsafe)

        """
        processes = []
        print("Executing with {} processors.".format(self.PROCESSES))
        # Assign task to threads
        for n in range(max(self.PROCESSES,1)):
            p = multiprocessing.Process(\
                target=_execute_synchronously,args=[self.test_queue,self,
                                                    timeout_per_test_sec])
            processes.append(p)
            p.start()
        while not _all_processes_are_dead(processes):
            if not self.print_queue.empty():
                print(self.print_queue.get())
            if not self.passed.empty():
                print(self.passed.get())
                self.count+=1
        for p in processes:
            p.join()
        while not self.print_queue.empty():
            print(self.print_queue.get())
        while not self.passed.empty():
            print(self.passed.get())
            self.count += 1
        print("passed {}/{}".format(self.count, self.total))
        return None
        

# quick and dirty static singleton
# might not work correctly if python has singly-inclusion
# like #pragma once in c++ headers
UTEST_INSTANCE = UnitTest()

def is_debug(name = __name__):
    """
        Safely encapsulates debug-only region.
        This further evaluates if __name__ is __mp_main__
        or __main_mp__ because multiprocessing
        requires some functions to appear
        when __name__ == __mp_main__ or __main_mp__
    """
    DEBUG_SYMBOLS = {"__main__","__mp_main__","__main_mp__"}
    is_de = name in DEBUG_SYMBOLS
    return is_de

def use_multithreading():
    """
        If you plan on using execute_async, put this function
        on top of your __main__ script. Otherwise, execute_async
        might not work correctly.
    """
    if __name__ == "__main__":
        multiprocessing.freeze_support()

# multiprocessing requires funcs to be defined in __main_mp__
# or __mp_main__
if is_debug():
    use_multithreading();
    def test_func(inp):
        if type(inp) is str:
            raise ZeroDivisionError
        return 2
    #tests that test for va-func transformation
    def test_func_2_args(arg1, arg2):
        return "{}_;_{}".format(arg1, arg2)
  
    def division(arg1, arg2):
        return arg1/arg2

    def return_1_increment(val):
        return val+1

    def test_dict_ret_inc(min,max,r=5):
        ret_val = dict()
        for i in range(min,max,r):
            ret_val[(i,)]=i+1
        return ret_val
# example usage
    def add_tests(UTEST_INSTANCE):
        UTEST_INSTANCE.add_test(test_func,2, 2)
        UTEST_INSTANCE.add_test(test_func, "2", "2")
        UTEST_INSTANCE.add_test(test_func, 1, 1)
        # expecting: 1/3 with one zerodivisionerror err msg


        UTEST_INSTANCE.add_test(test_func_2_args,\
            test_func_2_args(12,34),12,34)  #correct
        UTEST_INSTANCE.add_test(division, "2.5",5,2)  #correct
        # expecting another zerodivisionerror err msg.
        UTEST_INSTANCE.add_test(division,"inf",1,0)  #err
        # total should be 3/6
    
        entries = TestEntry.multi_init(return_1_increment,\
            int.__eq__,test_dict_ret_inc(0,1000,2),get_each_equal_rhs=True)
        UTEST_INSTANCE.add_tests(*entries)

        # Expect (max/range)+3 / (max/range)+6

    if __name__ == "__main__":
        #sync_utest = UnitTest()
        #add_tests(sync_utest)
        #sync_utest.execute()
        add_tests(UTEST_INSTANCE)
        #Expect the execution facing a deadlock somewhere.
        UTEST_INSTANCE.execute_async()
