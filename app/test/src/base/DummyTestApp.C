//* This file is part of the MOOSE framework
//* https://www.mooseframework.org
//*
//* All rights reserved, see COPYRIGHT for full restrictions
//* https://github.com/idaholab/moose/blob/master/COPYRIGHT
//*
//* Licensed under LGPL 2.1, please see LICENSE for details
//* https://www.gnu.org/licenses/lgpl-2.1.html
#include "DummyTestApp.h"
#include "DummyApp.h"
#include "Moose.h"
#include "AppFactory.h"
#include "MooseSyntax.h"

InputParameters
DummyTestApp::validParams()
{
  InputParameters params = DummyApp::validParams();
  params.set<bool>("use_legacy_material_output") = false;
  params.set<bool>("use_legacy_initial_residual_evaluation_behavior") = false;
  return params;
}

DummyTestApp::DummyTestApp(InputParameters parameters) : MooseApp(parameters)
{
  DummyTestApp::registerAll(
      _factory, _action_factory, _syntax, getParam<bool>("allow_test_objects"));
}

DummyTestApp::~DummyTestApp() {}

void
DummyTestApp::registerAll(Factory & f, ActionFactory & af, Syntax & s, bool use_test_objs)
{
  DummyApp::registerAll(f, af, s);
  if (use_test_objs)
  {
    Registry::registerObjectsTo(f, {"DummyTestApp"});
    Registry::registerActionsTo(af, {"DummyTestApp"});
  }
}

void
DummyTestApp::registerApps()
{
  registerApp(DummyApp);
  registerApp(DummyTestApp);
}

/***************************************************************************************************
 *********************** Dynamic Library Entry Points - DO NOT MODIFY ******************************
 **************************************************************************************************/
// External entry point for dynamic application loading
extern "C" void
DummyTestApp__registerAll(Factory & f, ActionFactory & af, Syntax & s)
{
  DummyTestApp::registerAll(f, af, s);
}
extern "C" void
DummyTestApp__registerApps()
{
  DummyTestApp::registerApps();
}
