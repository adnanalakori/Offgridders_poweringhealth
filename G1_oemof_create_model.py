import logging
import oemof.solph as solph
import oemof.outputlib as outputlib
from G2a_oemof_busses_and_componets import generate
import G2b_constraints_custom as constraints

class oemof_model:

    def load_energysystem_lp():
        # based on lp file
        return

    def build(experiment, case_dict):
        logging.debug('Initialize energy system dataframe')

        # create energy system
        micro_grid_system = solph.EnergySystem(timeindex=experiment['date_time_index'])

        #------        fuel and electricity bus------#
        bus_fuel = solph.Bus(label="bus_fuel")
        bus_electricity_mg = solph.Bus(label="bus_electricity_mg")
        micro_grid_system.add(bus_electricity_mg, bus_fuel)

        #------        fuel source------#
        #  todo can be without limit if constraint is inluded
        # todo define total_demand as entry of experiment eraly on! needed for generatemodel.fuel_oem

        if case_dict['genset_fixed_capacity'] == False:
            generate.fuel_oem(micro_grid_system, bus_fuel, experiment)
        elif isinstance(case_dict['genset_fixed_capacity'], float):
            generate.fuel_fix(micro_grid_system, bus_fuel, experiment)
        else:
            pass

        #------        demand sink ------#
        sink_demand = generate.demand(micro_grid_system, bus_electricity_mg, experiment['demand_profile'])

        #------        excess sink------#
        generate.excess(micro_grid_system, bus_electricity_mg)

        #------        pv ------#
        if case_dict['pv_fixed_capacity']==None:
            solar_plant = None
        elif case_dict['pv_fixed_capacity']==False:
            solar_plant = generate.pv_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict['pv_fixed_capacity'], float):
            solar_plant = generate.pv_fix(micro_grid_system, bus_electricity_mg, experiment,
                            capacity_pv=case_dict['pv_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at pv_fixed_capacity. Value can only be False, float or None')

        #------  wind  ------#
        if case_dict['wind_fixed_capacity']==None:
            wind_plant = None
        elif case_dict['wind_fixed_capacity']==False:
            wind_plant = generate.wind_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict['wind_fixed_capacity'], float):
            wind_plant = generate.wind_fix(micro_grid_system, bus_electricity_mg, experiment,
                            capacity_wind=case_dict['wind_fixed_capacity'])

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at wind_fixed_capacity. Value can only be False, float or None')

        #------         genset------#
        if case_dict['genset_fixed_capacity'] == None:
            genset = None
        elif case_dict['genset_fixed_capacity'] == False:
            if case_dict['genset_with_minimal_loading']==True:
                genset = generate.genset_oem_minload(micro_grid_system, bus_fuel, bus_electricity_mg, experiment)
            else:
                genset = generate.genset_oem(micro_grid_system, bus_fuel, bus_electricity_mg, experiment)

        elif isinstance(case_dict['genset_fixed_capacity'], float):
            if case_dict['genset_with_minimal_loading'] == True:
                genset = generate.genset_fix_minload(micro_grid_system, bus_fuel,
                                                             bus_electricity_mg, experiment,
                                                             capacity_fuel_gen=case_dict['genset_fixed_capacity'])
            else:
                genset = generate.genset_fix(micro_grid_system, bus_fuel,
                                                             bus_electricity_mg, experiment,
                                                             capacity_fuel_gen=case_dict['genset_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------storage------#
        if case_dict['storage_fixed_capacity'] == None:
            generic_storage = None
        elif case_dict['storage_fixed_capacity'] == False:
            generic_storage = generate.storage_oem(micro_grid_system, bus_electricity_mg, experiment)

        elif isinstance(case_dict['storage_fixed_capacity'], float):
            generic_storage = generate.storage_fix(micro_grid_system, bus_electricity_mg, experiment,
                                           capacity_storage=case_dict['storage_fixed_capacity']) # changed order

        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------     main grid bus and subsequent sources if necessary------#
        if case_dict['pcc_consumption_fixed_capacity'] != None or case_dict['pcc_feedin_fixed_capacity'] != None:
            bus_electricity_ng = solph.Bus(label="bus_electricity_ng")
            micro_grid_system.add(bus_electricity_ng)

        if case_dict['pcc_consumption_fixed_capacity'] != None:
            # source + sink for electricity from grid
            generate.maingrid_consumption(micro_grid_system, bus_electricity_ng, experiment)

        if case_dict['pcc_feedin_fixed_capacity'] != None:
            # sink + source for feed-in
            generate.maingrid_feedin(micro_grid_system, bus_electricity_ng, experiment)

        # ------        point of coupling (consumption) ------#
        if case_dict['pcc_consumption_fixed_capacity'] == None:
            pointofcoupling_consumption = None
        elif case_dict['pcc_consumption_fixed_capacity'] == False:
            # todo no minimal?
            # todo min_cap_pointofcoupling should be entry in case_dict
            pointofcoupling_consumption = generate.pointofcoupling_consumption_oem(micro_grid_system, bus_electricity_mg,
                                                                                   bus_electricity_ng, experiment,
                                                                                   min_cap_pointofcoupling=case_dict['peak_demand'])
        elif isinstance(case_dict['pcc_consumption_fixed_capacity'], float):
            pointofcoupling_consumption = generate.pointofcoupling_consumption_fix(micro_grid_system, bus_electricity_mg,
                                                                                   bus_electricity_ng, experiment,
                                                                                   cap_pointofcoupling=case_dict['pcc_consumption_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')


        #------point of coupling (feedin)------#
        if case_dict['pcc_feedin_fixed_capacity'] == None:
            pointofcoupling_feedin = None
        elif case_dict['pcc_feedin_fixed_capacity'] == False:
            # todo no minimal?
            generate.pointofcoupling_feedin_oem(micro_grid_system, bus_electricity_mg,
                                                                         bus_electricity_ng, experiment,
                                                                         min_cap_pointofcoupling=case_dict['peak_demand'])

        elif isinstance(case_dict['pcc_feedin_fixed_capacity'], float):
            generate.pointofcoupling_feedin_fix(micro_grid_system, bus_electricity_mg,
                                                                         bus_electricity_ng, experiment,
                                                                         capacity_pointofcoupling=case_dict['pcc_feedin_fixed_capacity'])
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at genset_fixed_capacity. Value can only be False, float or None')

        #------Optional: Shortage source'''
        if case_dict['allow_shortage'] == True:
            source_shortage = generate.shortage(micro_grid_system, bus_electricity_mg, experiment, case_dict) # changed order
        else:
            source_shortage = None

        logging.debug('Initialize the energy system to be optimized')
        model = solph.Model(micro_grid_system)

        if case_dict['stability_constraint'] == False:
            pass
        elif isinstance(case_dict['stability_constraint'], float):
            logging.debug('Adding stability constraint.')
            constraints.stability_criterion(model, case_dict,
                                            experiment = experiment,
                                            storage = generic_storage,
                                            sink_demand = sink_demand,
                                            genset = genset,
                                            pcc_consumption = pointofcoupling_consumption,
                                            source_shortage=source_shortage,
                                            el_bus = bus_electricity_mg)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at stability_constraint. Value can only be False, float or None')
        '''
        # todo: add wind plant
        if case_dict['renewable_share_constraint']==False:
            pass
        elif isinstance(case_dict['renewable_share_constraint'], float):
            logging.info('Adding renewable share constraint.')
            constraints.renewable_share_criterion(model,
                                                  experiment = experiment,
                                                  genset = genset,
                                                  pcc_consumption = pointofcoupling_consumption,
                                                  solar_plant=solar_plant,
                                                  el_bus=bus_electricity_mg)
        else:
            logging.warning('Case definition of ' + case_dict['case_name']
                            + ' faulty at stability_constraint. Value can only be False, float or None')
        '''
        return micro_grid_system, model

    def simulate(experiment, micro_grid_system, model, file_name):
        logging.debug('Solve the optimization problem')
        model.solve(solver          =   experiment['solver'],
                    solve_kwargs    =   {'tee': experiment['solver_verbose']}, # if tee_switch is true solver messages will be displayed
                    cmdline_options =   {experiment['cmdline_option']:    str(experiment['cmdline_option_value'])})   #ratioGap allowedGap mipgap

        if experiment['setting_save_lp_file'] == True:
            model.write(experiment['output_folder'] + '/lp_files/model_' + file_name + '.lp',
                        io_options={'symbolic_solver_labels': True})

        # add results to the energy system to make it possible to store them.
        micro_grid_system.results['main'] = outputlib.processing.results(model)
        micro_grid_system.results['meta'] = outputlib.processing.meta_results(model)
        return micro_grid_system

    def store_results(micro_grid_system, file_name, output_folder, setting_save_oemofresults):
        # store energy system with results
        if setting_save_oemofresults == True:
            micro_grid_system.dump(dpath=output_folder+'/oemof', filename = file_name + ".oemof" )
            logging.debug('Stored results in ' + output_folder+'/oemof' + '/' + file_name + ".oemof")
        return micro_grid_system

    def load_oemof_results(output_folder, file_name):
        logging.debug('Restore the energy system and the results.')
        micro_grid_system = solph.EnergySystem()
        micro_grid_system.restore(dpath=output_folder+'/oemof',
                                  filename=file_name + ".oemof")
        return micro_grid_system