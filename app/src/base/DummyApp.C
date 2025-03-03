#include "DummyApp.h"
#include "Moose.h"
#include "AppFactory.h"
#include "ModulesApp.h"
#include "MooseSyntax.h"

InputParameters
DummyApp::validParams()
{
  InputParameters params = MooseApp::validParams();
  params.set<bool>("use_legacy_material_output") = false;
  params.set<bool>("use_legacy_initial_residual_evaluation_behavior") = false;
  return params;
}

DummyApp::DummyApp(InputParameters parameters) : MooseApp(parameters)
{
  DummyApp::registerAll(_factory, _action_factory, _syntax);
}

DummyApp::~DummyApp() {}

void
DummyApp::registerAll(Factory & f, ActionFactory & af, Syntax & syntax)
{
  ModulesApp::registerAllObjects<DummyApp>(f, af, syntax);
  Registry::registerObjectsTo(f, {"DummyApp"});
  Registry::registerActionsTo(af, {"DummyApp"});

  /* register custom execute flags, action syntax, etc. here */
}

void
DummyApp::registerApps()
{
  registerApp(DummyApp);
}

/***************************************************************************************************
 *********************** Dynamic Library Entry Points - DO NOT MODIFY ******************************
 **************************************************************************************************/
extern "C" void
DummyApp__registerAll(Factory & f, ActionFactory & af, Syntax & s)
{
  DummyApp::registerAll(f, af, s);
}
extern "C" void
DummyApp__registerApps()
{
  DummyApp::registerApps();
}
