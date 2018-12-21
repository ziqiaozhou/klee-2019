//===-- main.cpp ------------------------------------------------*- C++ -*-===//
//
//                     The KLEE Symbolic Virtual Machine
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//

#include "expr/Lexer.h"
#include "expr/Parser.h"
#include <stp/c_interface.h>
#include "klee/Config/Version.h"
#include "klee/Constraints.h"
#include "klee/Expr.h"
#include "klee/ExprBuilder.h"
#include "klee/Solver.h"
#include "klee/SolverImpl.h"
#include "klee/Statistics.h"
#include "klee/SolverCmdLine.h"
#include "klee/Common.h"
#include "klee/util/ExprPPrinter.h"
#include "klee/util/ExprVisitor.h"
#include "klee/util/ExprSMTLIBPrinter.h"
#include "klee/Internal/Support/PrintVersion.h"

#include "llvm/ADT/StringExtras.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/ManagedStatic.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/raw_ostream.h"


#include <sys/stat.h>
#include <unistd.h>
#include<fstream>
#include<iostream>
#include<string>
#include "llvm/Support/Signals.h"

#if LLVM_VERSION_CODE < LLVM_VERSION(3, 5)
#include "llvm/ADT/OwningPtr.h"
#include "llvm/Support/system_error.h"
#endif

using namespace llvm;
using namespace klee;
using namespace klee::expr;

namespace {
  llvm::cl::opt<std::string>
  InputFile(llvm::cl::desc("<input query log>"), llvm::cl::Positional,
            llvm::cl::init("-"));
  enum ToolActions {
    PrintTokens,
    PrintAST,
    PrintSMTLIBv2,
    Evaluate,
	Merge,
	PrintCVC,
	ToCNF
  };
  static llvm::cl::opt<ToolActions> 
  ToolAction(llvm::cl::desc("Tool actions:"),
             llvm::cl::init(Evaluate),
             llvm::cl::values(
             clEnumValN(PrintTokens, "print-tokens",
                        "Print tokens from the input file."),
			clEnumValN(PrintSMTLIBv2, "print-smtlib",
					   "Print parsed input file as SMT-LIBv2 query."),
             clEnumValN(PrintAST, "print-ast",
                        "Print parsed AST nodes from the input file."),
             clEnumValN(Evaluate, "evaluate",
                        "Print parsed AST nodes from the input file."),
             clEnumValN(Merge, "merge",
				 "Merge parsed AST nodes from the input file."),
			 clEnumValN(ToCNF, "toCNF",
				 "Convert parsed AST nodes to CNF"),
			 clEnumValN(PrintCVC, "printCVC",
				 "Convert parsed AST nodes to CVC")

			 KLEE_LLVM_CL_VAL_END));
  static llvm::cl::list<std::string>
	  Kqueries(cl::Positional,
				  cl::desc("link kquery file"),
				  cl::value_desc("kquery files"),
				  cl::ZeroOrMore);
  llvm::cl::opt<std::string>
	  outFormat("outFormat",llvm::cl::desc("<output format>:kquery, cvc"),
				  llvm::cl::init("kquery"));


  enum BuilderKinds {
    DefaultBuilder,
    ConstantFoldingBuilder,
    SimplifyingBuilder
  };

  static llvm::cl::opt<BuilderKinds> 
  BuilderKind("builder",
              llvm::cl::desc("Expression builder:"),
              llvm::cl::init(DefaultBuilder),
              llvm::cl::values(
              clEnumValN(DefaultBuilder, "default",
                         "Default expression construction."),
              clEnumValN(ConstantFoldingBuilder, "constant-folding",
                         "Fold constant expressions."),
              clEnumValN(SimplifyingBuilder, "simplify",
                         "Fold constants and simplify expressions.")
              KLEE_LLVM_CL_VAL_END));


  llvm::cl::opt<std::string> directoryToWriteQueryLogs("query-log-dir",llvm::cl::desc("The folder to write query logs to. Defaults is current working directory."),
		                                               llvm::cl::init("."));

  llvm::cl::opt<bool> ClearArrayAfterQuery(
      "clear-array-decls-after-query",
      llvm::cl::desc("We discard the previous array declarations after a query "
                     "is performed. Default: false"),
	  llvm::cl::init(false));
}
static ExprHandle createAnd(std::vector<ExprHandle> kids,ExprBuilder * builder){
	unsigned n_kids = kids.size();
	assert(n_kids);
	if (n_kids == 1)
	  return kids[0];

	ExprHandle r = builder->And(kids[n_kids-2], kids[n_kids-1]);
	for (int i=n_kids-3; i>=0; i--)
	  r = builder->And(kids[i], r);
	return r;
}
static ExprHandle createOr(std::vector<ExprHandle> kids,ExprBuilder * builder){
	unsigned n_kids = kids.size();
	assert(n_kids);
	if (n_kids == 1)
	  return kids[0];

	ExprHandle r = builder->Or(kids[n_kids-2], kids[n_kids-1]);
	for (int i=n_kids-3; i>=0; i--)
	  r = builder->Or(kids[i], r);
	return r;
}

static std::string getQueryLogPath(const char filename[])
{
	//check directoryToWriteLogs exists
	struct stat s;
	if( !(stat(directoryToWriteQueryLogs.c_str(),&s) == 0 && S_ISDIR(s.st_mode)) )
	{
          llvm::errs() << "Directory to log queries \""
                       << directoryToWriteQueryLogs << "\" does not exist!"
                       << "\n";
          exit(1);
        }

	//check permissions okay
	if( !( (s.st_mode & S_IWUSR) && getuid() == s.st_uid) &&
	    !( (s.st_mode & S_IWGRP) && getgid() == s.st_gid) &&
	    !( s.st_mode & S_IWOTH)
	)
	{
          llvm::errs() << "Directory to log queries \""
                       << directoryToWriteQueryLogs << "\" is not writable!"
                       << "\n";
          exit(1);
        }

	std::string path=directoryToWriteQueryLogs;
	path+="/";
	path+=filename;
	return path;
}

static std::string escapedString(const char *start, unsigned length) {
  std::string Str;
  llvm::raw_string_ostream s(Str);
  for (unsigned i=0; i<length; ++i) {
    char c = start[i];
    if (isprint(c)) {
      s << c;
    } else if (c == '\n') {
      s << "\\n";
    } else {
      s << "\\x" 
        << hexdigit(((unsigned char) c >> 4) & 0xF) 
        << hexdigit((unsigned char) c & 0xF);
    }
  }
  return s.str();
}

static void PrintInputTokens(const MemoryBuffer *MB) {
  Lexer L(MB);
  Token T;
  do {
    L.Lex(T);
    llvm::outs() << "(Token \"" << T.getKindName() << "\" "
                 << "\"" << escapedString(T.start, T.length) << "\" "
                 << T.length << " " << T.line << " " << T.column << ")\n";
  } while (T.kind != Token::EndOfFile);
}

static bool PrintInputAST(const char *Filename,
                          const MemoryBuffer *MB,
                          ExprBuilder *Builder) {
  std::vector<Decl*> Decls;
  Parser *P = Parser::Create(Filename, MB, Builder, ClearArrayAfterQuery);
  P->SetMaxErrors(20);

  unsigned NumQueries = 0;
  while (Decl *D = P->ParseTopLevelDecl()) {
    if (!P->GetNumErrors()) {
      if (isa<QueryCommand>(D))
        llvm::outs() << "# Query " << ++NumQueries << "\n";

      D->dump();
    }
    Decls.push_back(D);
  }

  bool success = true;
  if (unsigned N = P->GetNumErrors()) {
    llvm::errs() << Filename << ": parse failure: " << N << " errors.\n";
    success = false;
  }

  for (std::vector<Decl*>::iterator it = Decls.begin(),
         ie = Decls.end(); it != ie; ++it)
    delete *it;

  delete P;

  return success;
}
static bool AST2CNF(const char *Filename,
                             const MemoryBuffer *MB,
                             ExprBuilder *Builder) {
	std::vector<Decl*> Decls;
	Parser *P = Parser::Create(Filename, MB, Builder, ClearArrayAfterQuery);
		P->SetMaxErrors(20);
		while (Decl *D = P->ParseTopLevelDecl()) {
			Decls.push_back(D);
		}

		bool success = true;
		if (unsigned N = P->GetNumErrors()) {
			llvm::errs() << Filename << ": parse failure: " << N << " errors.\n";
			success = false;
		}  

		if (!success)
		  return false;

		Solver *coreSolver = klee::createCoreSolver(CoreSolverToUse);

		if (CoreSolverToUse != DUMMY_SOLVER) {
			const time::Span maxCoreSolverTime(MaxCoreSolverTime);
			if (maxCoreSolverTime) {
				coreSolver->setCoreSolverTimeout(maxCoreSolverTime);
			}
		}

		Solver *S = constructSolverChain(coreSolver,
					getQueryLogPath(ALL_QUERIES_SMT2_FILE_NAME),
					getQueryLogPath(SOLVER_QUERIES_SMT2_FILE_NAME),
					getQueryLogPath(ALL_QUERIES_KQUERY_FILE_NAME),
					getQueryLogPath(SOLVER_QUERIES_KQUERY_FILE_NAME));

		unsigned Index = 0;
		for (std::vector<Decl*>::iterator it = Decls.begin(),
					ie = Decls.end(); it != ie; ++it) {
			Decl *D = *it;
			if (QueryCommand *QC = dyn_cast<QueryCommand>(D)) {
				llvm::outs() << "Query " << Index << ":\t";
				if (QC->Values.empty() && QC->Objects.empty()) {
					bool result;
					S->mustBeTrue(Query(ConstraintManager(QC->Constraints), QC->Query),
									result);
				} else if (!QC->Values.empty()) {
					ref<ConstantExpr> result;
					S->getValue(Query(ConstraintManager(QC->Constraints), 
										QC->Values[0]),
									result);
				} else {
					std::vector< std::vector<unsigned char> > result;
					S->getInitialValues(Query(ConstraintManager(QC->Constraints), 
									QC->Query),
								QC->Objects, result);
				}
				llvm::outs() << "\n";
				++Index;
			}
		}

		for (std::vector<Decl*>::iterator it = Decls.begin(),
					ie = Decls.end(); it != ie; ++it)
		  delete *it;
		delete P;

		delete S;

		return success;

}
static bool printInputAsCVC(const char *Filename,
                             const MemoryBuffer *MB,
                             ExprBuilder *Builder)
{
	//Parse the input file
	std::vector<Decl*> Decls;
        Parser *P = Parser::Create(Filename, MB, Builder, ClearArrayAfterQuery);
        P->SetMaxErrors(20);
	while (Decl *D = P->ParseTopLevelDecl())
	{
		Decls.push_back(D);
	}

	bool success = true;
	if (unsigned N = P->GetNumErrors())
	{
		llvm::errs() << Filename << ": parse failure: "
				   << N << " errors.\n";
		success = false;
	}

	if (!success)
	return false;
	unsigned int queryNumber = 0;

	Solver *coreSolver = klee::createCoreSolver(CoreSolverToUse);
	//Loop over the declarations
	for (std::vector<Decl*>::iterator it = Decls.begin(), ie = Decls.end(); it != ie; ++it)
	{
		Decl *D = *it;
		if (QueryCommand *QC = dyn_cast<QueryCommand>(D))
		{
			//print line break to separate from previous query
			if(queryNumber!=0) 	llvm::outs() << "\n";

			//Output header for this query as a SMT-LIBv2 comment
			llvm::outs() << ";SMTLIBv2 Query " << queryNumber << "\n";

			/* Can't pass ConstraintManager constructor directly
			 * as argument to Query object. Like...
			 * query(ConstraintManager(QC->Constraints),QC->Query);
			 *
			 * For some reason if constructed this way the first
			 * constraint in the constraint set is set to NULL and
			 * will later cause a NULL pointer dereference.
			 */
			ConstraintManager constraintM(QC->Constraints);
			Query query(constraintM,QC->Query);
			std::ofstream f;
			std::stringstream s;
			s<<"result_"<<queryNumber<<".cvc";
			f.open(s.str());
			f<<coreSolver->getConstraintLog(query);
			f.close();
			queryNumber++;
		}
	}

	//Clean up
	for (std::vector<Decl*>::iterator it = Decls.begin(),
			ie = Decls.end(); it != ie; ++it)
		delete *it;
	delete P;

	if(outFormat=="cvc"){
	}

	return true;
}
static bool mergeAST2CNF(const char *Filename,
			const MemoryBuffer *MB,
			ExprBuilder *Builder,std::string outFormat) {
	std::vector<Decl*> Decls;
	std::vector<ExprHandle> OrExprVec;
	std::vector<std::string>::iterator pcs_it,pc_end;
	QueryCommand* mainQC;
	std::vector<Parser*> allP;
	Parser *P = Parser::Create(Filename, MB, Builder, ClearArrayAfterQuery);
	allP.push_back(P);
	P->SetMaxErrors(20);
	Solver *coreSolver = klee::createCoreSolver(CoreSolverToUse);


	std::vector<ExprHandle> mainConstraints;
	while (Decl *D = P->ParseTopLevelDecl()) {

		if (ArrayDecl *QC = dyn_cast<ArrayDecl>(D)) {
			Decls.push_back(QC);
		}else if (QueryCommand *QC = dyn_cast<QueryCommand>(D)) {
			mainQC=QC;
			for(unsigned k=0;k<QC->Constraints.size();k++){
				klee::ref<klee::Expr> expr=static_cast<klee::ref<klee::Expr>>((QC->Constraints)[k]);
				mainConstraints.push_back(expr);
			}
		}
	}
	OrExprVec.push_back(createAnd(mainConstraints,Builder));
	bool success = true;
	if (unsigned N = P->GetNumErrors()) {
		llvm::errs() << Filename << ": parse failure: " << N << " errors.\n";
		success = false;
	}  
	if (!success)
	  return false;

	for(pcs_it=Kqueries.begin(),pc_end=Kqueries.end();pcs_it!=pc_end;++pcs_it){
		const char * filename=pcs_it->c_str();
		llvm::outs()<<"filename="<<filename<<"\n";
#if LLVM_VERSION_CODE < LLVM_VERSION(3,5)
		OwningPtr<MemoryBuffer> MB0;
		error_code ec=MemoryBuffer::getFileOrSTDIN(filename, MB0);
		if (ec) {
			llvm::errs() << ": error: " << ec.message() << "\n";
			return 1;
		}
#else
		auto MBResult = MemoryBuffer::getFileOrSTDIN(filename);
		if (!MBResult) {
			llvm::errs()  << ": error: " << MBResult.getError().message()
				<< "\n";
			return 1;
		}
		std::unique_ptr<MemoryBuffer> &MB0 = *MBResult;
#endif
		P = Parser::Create(filename, MB0.get(), Builder, ClearArrayAfterQuery);
		P->SetMaxErrors(20);
		ExprHandle AndExpr;
		std::vector<ExprHandle> Constraints;
		Constraints.clear();
		while (Decl *D = P->ParseTopLevelDecl()) {
			if (ArrayDecl *QC = dyn_cast<ArrayDecl>(D)) {
				Decls.push_back(QC);
			}else if (QueryCommand *QC = dyn_cast<QueryCommand>(D)) {
				for(unsigned k=0;k<QC->Constraints.size();k++){
					klee::ref<klee::Expr> expr=static_cast<klee::ref<klee::Expr>>((QC->Constraints)[k]);
					Constraints.push_back(expr);
				}
			}
		}

		OrExprVec.push_back(createAnd(Constraints,Builder));
		success = true;
		if (unsigned N = P->GetNumErrors()) {
			llvm::errs() << Filename << ": parse failure: " << N << " errors.\n";
			success = false;
		}  
		if (!success){
			return false;
		}
	}
	ExprHandle finalExpr=createOr(OrExprVec,Builder);

	ConstraintManager cm;
	cm.addConstraint(finalExpr);
	if(outFormat=="kquery"){
		std::vector<ExprHandle> cs;
		cs.push_back(finalExpr);
		QueryCommand * allQC=new QueryCommand(cs, mainQC->Query,mainQC->Values, mainQC->Objects);

		llvm::outs()<<"#merge finished"<<"\n";
		std::map<std::string,bool> declMap;
		for (std::vector<Decl*>::iterator it = Decls.begin(),
					ie = Decls.end(); it != ie; ++it) {
			Decl *D = *it;
			if (ArrayDecl *QC = dyn_cast<ArrayDecl>(D)) {
				std::string name=QC->Root->name;
				llvm::errs()<<name;
				if (declMap.count(name))
				  continue;
				declMap[name]=true;
				QC->dump();
			}
		}
		allQC->dump();
	}

	//bool result;

	return success;
}
static bool EvaluateInputAST(const char *Filename,
			const MemoryBuffer *MB,
			ExprBuilder *Builder) {
	std::vector<Decl*> Decls;
	Parser *P = Parser::Create(Filename, MB, Builder, ClearArrayAfterQuery);
		P->SetMaxErrors(20);
		while (Decl *D = P->ParseTopLevelDecl()) {
			Decls.push_back(D);
		}

		bool success = true;
		if (unsigned N = P->GetNumErrors()) {
			llvm::errs() << Filename << ": parse failure: " << N << " errors.\n";
			success = false;
		}  

		if (!success)
		  return false;

		Solver *coreSolver = klee::createCoreSolver(CoreSolverToUse);

		if (CoreSolverToUse != DUMMY_SOLVER) {
			const time::Span maxCoreSolverTime(MaxCoreSolverTime);
			if (maxCoreSolverTime) {
				coreSolver->setCoreSolverTimeout(maxCoreSolverTime);
			}
		}

		Solver *S = constructSolverChain(coreSolver,
					getQueryLogPath(ALL_QUERIES_SMT2_FILE_NAME),
					getQueryLogPath(SOLVER_QUERIES_SMT2_FILE_NAME),
					getQueryLogPath(ALL_QUERIES_KQUERY_FILE_NAME),
					getQueryLogPath(SOLVER_QUERIES_KQUERY_FILE_NAME));

		unsigned Index = 0;
		for (std::vector<Decl*>::iterator it = Decls.begin(),
					ie = Decls.end(); it != ie; ++it) {
			Decl *D = *it;
			if (QueryCommand *QC = dyn_cast<QueryCommand>(D)) {
				llvm::outs() << "Query " << Index << ":\t";

				assert("FIXME: Support counterexample query commands!");
				if (QC->Values.empty() && QC->Objects.empty()) {
					bool result;
					if (S->mustBeTrue(Query(ConstraintManager(QC->Constraints), QC->Query),
									result)) {
						llvm::outs() <<"QC empty"<< (result ? "VALID" : "INVALID");
					} else {
						llvm::outs() << "FAIL (reason: "
							<< SolverImpl::getOperationStatusString(S->impl->getOperationStatusCode())
							<< ")";
					}
				} else if (!QC->Values.empty()) {
					assert(QC->Objects.empty() && 
								"FIXME: Support counterexamples for values and objects!");
					assert(QC->Values.size() == 1 &&
								"FIXME: Support counterexamples for multiple values!");
					assert(QC->Query->isFalse() &&
								"FIXME: Support counterexamples with non-trivial query!");
					ref<ConstantExpr> result;
					if (S->getValue(Query(ConstraintManager(QC->Constraints), 
										QC->Values[0]),
									result)) {
						llvm::outs() << "INVALID\n";
						llvm::outs() << "\tExpr 0:\t" << result;
					} else {
						llvm::outs() << "FAIL (reason: "
							<< SolverImpl::getOperationStatusString(S->impl->getOperationStatusCode())
							<< ")";
					}
				} else {
					std::vector< std::vector<unsigned char> > result;

					if (S->getInitialValues(Query(ConstraintManager(QC->Constraints), 
										QC->Query),
									QC->Objects, result)) {
						llvm::outs() << "else INVALID\n";

						for (unsigned i = 0, e = result.size(); i != e; ++i) {
							llvm::outs() << "\tArray " << i << ":\t"
								<< QC->Objects[i]->name
								<< "[";
							for (unsigned j = 0; j != QC->Objects[i]->size; ++j) {
								llvm::outs() << (unsigned) result[i][j];
								if (j + 1 != QC->Objects[i]->size)
								  llvm::outs() << ", ";
							}
							llvm::outs() << "]";
							if (i + 1 != e)
							  llvm::outs() << "\n";
						}
					} else {
						SolverImpl::SolverRunStatus retCode = S->impl->getOperationStatusCode();
						if (SolverImpl::SOLVER_RUN_STATUS_TIMEOUT == retCode) {
							llvm::outs() << " FAIL (reason: "
								<< SolverImpl::getOperationStatusString(retCode)
								<< ")";
						}           
						else {
							llvm::outs() << "VALID (counterexample request ignored)";
						}
					}
				}

				llvm::outs() << "\n";
				++Index;
			}
		}

		for (std::vector<Decl*>::iterator it = Decls.begin(),
					ie = Decls.end(); it != ie; ++it)
		  delete *it;
		delete P;

		delete S;

		if (uint64_t queries = *theStatisticManager->getStatisticByName("Queries")) {
			llvm::outs()
				<< "--\n"
				<< "total queries = " << queries << "\n"
				<< "total queries constructs = " 
				<< *theStatisticManager->getStatisticByName("QueriesConstructs") << "\n"
				<< "valid queries = " 
				<< *theStatisticManager->getStatisticByName("QueriesValid") << "\n"
				<< "invalid queries = " 
				<< *theStatisticManager->getStatisticByName("QueriesInvalid") << "\n"
				<< "query cex = " 
				<< *theStatisticManager->getStatisticByName("QueriesCEX") << "\n";
		}

		return success;
	}

static bool printInputAsSMTLIBv2(const char *Filename,
                             const MemoryBuffer *MB,
                             ExprBuilder *Builder)
{
	//Parse the input file
	std::vector<Decl*> Decls;
        Parser *P = Parser::Create(Filename, MB, Builder, ClearArrayAfterQuery);
        P->SetMaxErrors(20);
	while (Decl *D = P->ParseTopLevelDecl())
	{
		Decls.push_back(D);
	}

	bool success = true;
	if (unsigned N = P->GetNumErrors())
	{
		llvm::errs() << Filename << ": parse failure: "
				   << N << " errors.\n";
		success = false;
	}

	if (!success)
	return false;

	ExprSMTLIBPrinter printer;
	printer.setOutput(llvm::outs());

	unsigned int queryNumber = 0;
	//Loop over the declarations
	for (std::vector<Decl*>::iterator it = Decls.begin(), ie = Decls.end(); it != ie; ++it)
	{
		Decl *D = *it;
		if (QueryCommand *QC = dyn_cast<QueryCommand>(D))
		{
			//print line break to separate from previous query
			if(queryNumber!=0) 	llvm::outs() << "\n";

			//Output header for this query as a SMT-LIBv2 comment
			llvm::outs() << ";SMTLIBv2 Query " << queryNumber << "\n";

			/* Can't pass ConstraintManager constructor directly
			 * as argument to Query object. Like...
			 * query(ConstraintManager(QC->Constraints),QC->Query);
			 *
			 * For some reason if constructed this way the first
			 * constraint in the constraint set is set to NULL and
			 * will later cause a NULL pointer dereference.
			 */
			ConstraintManager constraintM(QC->Constraints);
			Query query(constraintM,QC->Query);
			printer.setQuery(query);

			if(!QC->Objects.empty())
				printer.setArrayValuesToGet(QC->Objects);

			printer.generateOutput();


			queryNumber++;
		}
	}

	//Clean up
	for (std::vector<Decl*>::iterator it = Decls.begin(),
			ie = Decls.end(); it != ie; ++it)
		delete *it;
	delete P;

	return true;
}

int main(int argc, char **argv) {
  bool success = true;

#if LLVM_VERSION_CODE >= LLVM_VERSION(3, 9)
  llvm::sys::PrintStackTraceOnErrorSignal(argv[0]);
#else
  llvm::sys::PrintStackTraceOnErrorSignal();
#endif
  llvm::cl::SetVersionPrinter(klee::printVersion);
  llvm::cl::ParseCommandLineOptions(argc, argv);

  std::string ErrorStr;
  
#if LLVM_VERSION_CODE < LLVM_VERSION(3,5)
  OwningPtr<MemoryBuffer> MB;
  error_code ec=MemoryBuffer::getFileOrSTDIN(InputFile.c_str(), MB);
  if (ec) {
    llvm::errs() << argv[0] << ": error: " << ec.message() << "\n";
    return 1;
  }
#else
  auto MBResult = MemoryBuffer::getFileOrSTDIN(InputFile.c_str());
  if (!MBResult) {
    llvm::errs() << argv[0] << ": error: " << MBResult.getError().message()
                 << "\n";
    return 1;
  }
  std::unique_ptr<MemoryBuffer> &MB = *MBResult;
#endif
  
  ExprBuilder *Builder = 0;
  switch (BuilderKind) {
  case DefaultBuilder:
    Builder = createDefaultExprBuilder();
    break;
  case ConstantFoldingBuilder:
    Builder = createDefaultExprBuilder();
    Builder = createConstantFoldingExprBuilder(Builder);
    break;
  case SimplifyingBuilder:
    Builder = createDefaultExprBuilder();
    Builder = createConstantFoldingExprBuilder(Builder);
    Builder = createSimplifyingExprBuilder(Builder);
    break;
  }

  switch (ToolAction) {
  case PrintTokens:
    PrintInputTokens(MB.get());
    break;
  case PrintAST:
    success = PrintInputAST(InputFile=="-" ? "<stdin>" : InputFile.c_str(), MB.get(),
                            Builder);
    break;
  case Evaluate:
    success = EvaluateInputAST(InputFile=="-" ? "<stdin>" : InputFile.c_str(),
                               MB.get(), Builder);
	break;
  case Merge:
		success = mergeAST2CNF(
					InputFile=="-" ? "<stdin>" : InputFile.c_str(),
					MB.get(), 
					Builder,
					outFormat);
	break;
  case ToCNF:
		success = AST2CNF(InputFile=="-" ? "<stdin>" : InputFile.c_str(),
					MB.get(), Builder);
	break;

  case PrintSMTLIBv2:
    success = printInputAsSMTLIBv2(InputFile=="-"? "<stdin>" : InputFile.c_str(), MB.get(),Builder);
    break;
case PrintCVC:
    success = printInputAsCVC(InputFile=="-"? "<stdin>" : InputFile.c_str(), MB.get(),Builder);
	break;
  default:
    llvm::errs() << argv[0] << ": error: Unknown program action!\n";
  }

  delete Builder;
  llvm::llvm_shutdown();
  return success ? 0 : 1;
}
