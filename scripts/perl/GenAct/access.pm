#!/usr/bin/perl -w
###############################################
#
#	file: access.pm
#	date: 2008-06-30
#	module should be imported by different
#	perl file, in order to get one place
#	to change configuration data instead of
#	changing the data several times.
#
###############################################
use strict;

sub getServer
{
	return "localhost";
}
sub getUsername
{
	return "root";
}
sub getPassword
{
	return "xxx";
}
sub getDSN_VarGenAtt
{
	return "DBI:mysql:VarGenAtt_ActPh3:localhost";
}
sub getDSN_PotAncCL
{
	return "DBI:mysql:PotAncCL:localhost";
}
sub getDSN_GenealogyCL
{
	return "DBI:mysql:GenealogyCL:localhost";
}

1;
